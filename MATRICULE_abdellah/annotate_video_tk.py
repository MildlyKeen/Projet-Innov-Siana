"""
ANNOTATION AVEC INTERFACE TKINTER
==================================
Sélectionnez le matricule avec la souris directement sur l'image
"""

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import cv2
import json
import os

class VideoAnnotatorTk:
    def __init__(self, video_path, frames_to_annotate):
        self.video_path = video_path
        self.frames_to_annotate = frames_to_annotate
        self.current_frame_idx = 0
        self.annotations = []
        
        self.root = tk.Tk()
        self.root.title("Annotation Vidéo - Sélectionnez le Matricule")
        
        # Variables
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.current_image = None
        self.photo_image = None
        
        # Interface
        self.setup_ui()
        self.load_frame(self.frames_to_annotate[0])
        
    def setup_ui(self):
        # Frame info
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=10)
        
        self.frame_label = tk.Label(info_frame, text="", font=("Arial", 14, "bold"))
        self.frame_label.pack()
        
        # Canvas pour l'image
        self.canvas = tk.Canvas(self.root, cursor="cross")
        self.canvas.pack(padx=10, pady=10)
        
        # Événements souris
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # Contrôles
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)
        
        tk.Label(control_frame, text="Matricule:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        
        self.matricule_entry = tk.Entry(control_frame, font=("Arial", 12), width=10)
        self.matricule_entry.insert(0, "1203")
        self.matricule_entry.pack(side=tk.LEFT, padx=5)
        
        self.next_button = tk.Button(control_frame, text="Suivant →", 
                                      command=self.save_and_next,
                                      font=("Arial", 12), bg="#4CAF50", fg="white",
                                      padx=20, pady=5)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="Ignorer", 
                  command=self.skip_frame,
                  font=("Arial", 12), padx=20, pady=5).pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = tk.Label(self.root, 
                               text="Cliquez et glissez pour sélectionner le matricule | "
                                    "Entrez le matricule | Cliquez Suivant",
                               font=("Arial", 10), fg="gray")
        instructions.pack(pady=5)
        
        # Bbox info
        self.bbox_label = tk.Label(self.root, text="", font=("Arial", 10), fg="blue")
        self.bbox_label.pack()
    
    def load_frame(self, frame_number):
        """Charge une frame de la vidéo"""
        cap = cv2.VideoCapture(self.video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            messagebox.showerror("Erreur", f"Impossible de charger la frame {frame_number}")
            return
        
        # Convertir BGR -> RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.current_frame = frame_rgb.copy()
        
        # Redimensionner si trop grand
        height, width = frame_rgb.shape[:2]
        max_width = 1200
        max_height = 800
        
        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame_rgb = cv2.resize(frame_rgb, (new_width, new_height))
        
        self.display_width = frame_rgb.shape[1]
        self.display_height = frame_rgb.shape[0]
        self.scale_x = width / self.display_width
        self.scale_y = height / self.display_height
        
        # Convertir en PIL
        self.current_image = Image.fromarray(frame_rgb)
        self.display_image = self.current_image.copy()
        self.photo_image = ImageTk.PhotoImage(self.display_image)
        
        # Afficher
        self.canvas.config(width=self.display_width, height=self.display_height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
        
        # Mise à jour label
        self.frame_label.config(
            text=f"Frame {frame_number} ({self.current_frame_idx + 1}/{len(self.frames_to_annotate)})"
        )
        
        # Reset bbox
        self.current_bbox = None
        self.bbox_label.config(text="")
    
    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
    
    def on_drag(self, event):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline="lime", width=3
        )
    
    def on_release(self, event):
        end_x = event.x
        end_y = event.y
        
        # Normaliser
        x = min(self.start_x, end_x)
        y = min(self.start_y, end_y)
        w = abs(end_x - self.start_x)
        h = abs(end_y - self.start_y)
        
        # Convertir aux coordonnées originales
        orig_x = int(x * self.scale_x)
        orig_y = int(y * self.scale_y)
        orig_w = int(w * self.scale_x)
        orig_h = int(h * self.scale_y)
        
        self.current_bbox = [orig_x, orig_y, orig_w, orig_h]
        
        self.bbox_label.config(
            text=f"Bbox: [{orig_x}, {orig_y}, {orig_w}, {orig_h}]"
        )
    
    def save_and_next(self):
        if not self.current_bbox or self.current_bbox[2] == 0 or self.current_bbox[3] == 0:
            messagebox.showwarning("Attention", "Veuillez sélectionner une région")
            return
        
        matricule = self.matricule_entry.get().strip()
        if not matricule:
            messagebox.showwarning("Attention", "Veuillez entrer le matricule")
            return
        
        # Sauvegarder
        frame_num = self.frames_to_annotate[self.current_frame_idx]
        annotation = {
            'frame': frame_num,
            'bbox': self.current_bbox,
            'matricule': matricule
        }
        
        self.annotations.append(annotation)
        print(f"✓ Annotation {len(self.annotations)} sauvegardée:")
        print(f"  Frame: {frame_num}")
        print(f"  Bbox: {self.current_bbox}")
        print(f"  Matricule: {matricule}")
        
        # Frame suivante
        self.current_frame_idx += 1
        
        if self.current_frame_idx < len(self.frames_to_annotate):
            if self.rect_id:
                self.canvas.delete(self.rect_id)
                self.rect_id = None
            self.load_frame(self.frames_to_annotate[self.current_frame_idx])
        else:
            self.finish()
    
    def skip_frame(self):
        self.current_frame_idx += 1
        
        if self.current_frame_idx < len(self.frames_to_annotate):
            if self.rect_id:
                self.canvas.delete(self.rect_id)
                self.rect_id = None
            self.load_frame(self.frames_to_annotate[self.current_frame_idx])
        else:
            self.finish()
    
    def finish(self):
        # Sauvegarder les annotations
        if self.annotations:
            output_file = "video_annotations.json"
            data = {
                'video': os.path.basename(self.video_path),
                'annotations': self.annotations
            }
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print("\n" + "="*70)
            print(f"✓ {len(self.annotations)} annotations sauvegardées: {output_file}")
            print("="*70)
            
            messagebox.showinfo("Terminé", 
                              f"{len(self.annotations)} annotations sauvegardées!\n"
                              f"Fichier: {output_file}")
        else:
            messagebox.showwarning("Attention", "Aucune annotation sauvegardée")
        
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    video_path = r"C:\Users\abdel\OneDrive\Documents\GitHub\Projet-Innov-Siana\MATRICULE_abdellah\video entrainement OCR.mp4"
    frames = [30, 35, 40, 45]
    
    print("\n" + "="*70)
    print("ANNOTATION VIDÉO AVEC INTERFACE TKINTER")
    print("="*70)
    print("Instructions:")
    print("  1. Cliquez et glissez sur l'image pour sélectionner le matricule")
    print("  2. Entrez le matricule dans le champ")
    print("  3. Cliquez 'Suivant' pour passer à la frame suivante")
    print("="*70 + "\n")
    
    app = VideoAnnotatorTk(video_path, frames)
    app.run()
