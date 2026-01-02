from collections import defaultdict

def build_events_from_per_frame(rows, enter_n=3, exit_n=3, max_gap=1):
    """
    rows: liste de dicts issus de occupancy_per_frame.csv ou de fuse()
          champs attendus: frame, track_id, assigned_track, overlap

    enter_n: nb de frames validées pour déclarer une arrivée
    exit_n: nb de frames invalides pour déclarer un départ
    max_gap: tolérance trous courts (occlusion) : ex 1 frame
    """

    # --- regrouper par voie ---
    # On veut une timeline par voie : à chaque frame, quel track_id occupe la voie ?
    by_track = defaultdict(list)
    for r in rows:
        by_track[r["assigned_track"]].append(r)

    # Etat par voie
    state = {}  # voie -> dict
    events = []

    def init_track(label):
        state[label] = {
            "status": "libre",
            "current_track_id": None,
            "enter_count": 0,
            "exit_count": 0,
            "gap_count": 0,
            "start_frame": None,
        }

    # On veut itérer sur toutes les frames dans l’ordre
    frames = sorted(set(int(r["frame"]) for r in rows))
    # Liste des voies vues (hors None)
    tracks_seen = sorted(set(r["assigned_track"] for r in rows if r["assigned_track"] not in (None, "", "None")))

    for label in tracks_seen:
        init_track(label)

    # Pour accès rapide : (frame,label) -> track_id
    lookup = {}
    for r in rows:
        f = int(r["frame"])
        label = r["assigned_track"]
        if label in (None, "", "None"):
            continue
        # Si plusieurs trains sur même voie en même frame -> on garde celui avec overlap max
        key = (f, label)
        if key not in lookup:
            lookup[key] = r
        else:
            if float(r.get("overlap", 0)) > float(lookup[key].get("overlap", 0)):
                lookup[key] = r

    for f in frames:
        for label in tracks_seen:
            st = state[label]

            cur = lookup.get((f, label))  # dict ou None
            cur_track_id = int(cur["track_id"]) if cur else None

            if st["status"] == "libre":
                if cur_track_id is not None:
                    st["enter_count"] += 1
                    if st["enter_count"] == 1:
                        st["start_frame"] = f
                        st["current_track_id"] = cur_track_id

                    # si le track_id change pendant la phase d’entrée, on reset (évite bruit)
                    if st["current_track_id"] != cur_track_id:
                        st["enter_count"] = 1
                        st["start_frame"] = f
                        st["current_track_id"] = cur_track_id

                    if st["enter_count"] >= enter_n:
                        st["status"] = "occupée"
                        st["exit_count"] = 0
                        st["gap_count"] = 0

                        events.append({
                            "event": "ARRIVAL",
                            "state": "occupée",
                            "track": label,
                            "train_track_id": st["current_track_id"],
                            "start_frame": st["start_frame"],
                            "frame": f
                        })
                else:
                    st["enter_count"] = 0
                    st["current_track_id"] = None
                    st["start_frame"] = None

            else:  # occupée
                if cur_track_id is not None:
                    # si un autre track_id apparaît, on considère anomalie simple
                    if st["current_track_id"] != cur_track_id:
                        events.append({
                            "event": "ANOMALY",
                            "state": "anomalie",
                            "track": label,
                            "train_track_id": cur_track_id,
                            "frame": f,
                            "reason": "track_switch_on_same_track"
                        })
                        # on décide de switcher ou pas (MVP: on switch)
                        st["current_track_id"] = cur_track_id

                    st["exit_count"] = 0
                    st["gap_count"] = 0

                else:
                    st["gap_count"] += 1
                    if st["gap_count"] <= max_gap:
                        # tolérance petite occlusion : ne pas sortir tout de suite
                        continue

                    st["exit_count"] += 1
                    if st["exit_count"] >= exit_n:
                        events.append({
                            "event": "DEPARTURE",
                            "state": "libre",
                            "track": label,
                            "train_track_id": st["current_track_id"],
                            "end_frame": f,
                            "frame": f
                        })
                        # reset
                        st["status"] = "libre"
                        st["current_track_id"] = None
                        st["enter_count"] = 0
                        st["exit_count"] = 0
                        st["gap_count"] = 0
                        st["start_frame"] = None

    return events

def merge_close_occupancies(events, merge_gap=30, min_duration=20):
    """
    events: liste d'events ARRIVAL/DEPARTURE produits par build_events_from_per_frame
    merge_gap: si un ARRIVAL arrive <= merge_gap frames après un DEPARTURE, on fusionne
    min_duration: supprimer les occupancies trop courtes (durée < min_duration)

    Retourne une nouvelle liste d'events nettoyée.
    """
    # regrouper par voie
    by_track = {}
    for e in events:
        by_track.setdefault(e["track"], []).append(e)

    cleaned = []

    for track, evs in by_track.items():
        evs = sorted(evs, key=lambda x: x["frame"])
        # transformer en segments [start, end]
        segments = []
        current = None

        for e in evs:
            if e["event"] == "ARRIVAL":
                current = {
                    "track": track,
                    "train_track_id": e["train_track_id"],
                    "start_frame": e["start_frame"],
                    "arrival_frame": e["frame"],
                    "end_frame": None
                }
            elif e["event"] == "DEPARTURE" and current is not None:
                current["end_frame"] = e["end_frame"]
                segments.append(current)
                current = None

        # s'il reste une occupation ouverte
        if current is not None:
            segments.append(current)

        # fusionner les segments proches
        merged = []
        for s in segments:
            if not merged:
                merged.append(s)
                continue
            prev = merged[-1]

            # même voie + même train_track_id + petit gap => fusion
            prev_end = prev["end_frame"]
            s_start = s["start_frame"]
            if prev_end is not None and (s_start - prev_end) <= merge_gap and prev["train_track_id"] == s["train_track_id"]:
                # fusion : on étend la fin
                prev["end_frame"] = s["end_frame"]
            else:
                merged.append(s)

        # filtrer par durée
        for s in merged:
            if s["end_frame"] is not None:
                duration = s["end_frame"] - s["start_frame"]
                if duration < min_duration:
                    continue  # on jette les micro-occupations

            # reconstruire ARRIVAL/DEPARTURE propres
            cleaned.append({
                "event": "ARRIVAL",
                "state": "occupée",
                "track": s["track"],
                "train_track_id": s["train_track_id"],
                "start_frame": s["start_frame"],
                "frame": s["start_frame"] + 2  # conservateur, ou s["arrival_frame"]
            })
            if s["end_frame"] is not None:
                cleaned.append({
                    "event": "DEPARTURE",
                    "state": "libre",
                    "track": s["track"],
                    "train_track_id": s["train_track_id"],
                    "end_frame": s["end_frame"],
                    "frame": s["end_frame"]
                })

    return sorted(cleaned, key=lambda x: x["frame"])
