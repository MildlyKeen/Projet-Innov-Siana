# Smart Yard MVP 🚂

MVP pour le projet ferroviaire Smart Yard - Système de gestion ferroviaire intelligent avec visualisation en temps réel.

## 📋 Description

Smart Yard est une application web responsive développée avec React et Vite pour la gestion et la visualisation d'un système ferroviaire. L'application offre une interface moderne et intuitive pour surveiller :

- L'état des trains (actifs, en maintenance, disponibles)
- Le trafic ferroviaire sur 24 heures
- L'utilisation des voies
- L'état en temps réel de chaque voie

## 🚀 Technologies Utilisées

- **React 19.2** - Bibliothèque UI
- **Vite 7.2** - Build tool et dev server
- **Bootstrap 5.3** - Framework CSS responsive
- **Chart.js 4.5** - Bibliothèque de graphiques
- **react-chartjs-2 5.3** - Wrapper React pour Chart.js

## 📁 Structure du Projet

```
src/
├── components/
│   ├── Dashboard/        # Tableau de bord avec statistiques et graphiques
│   ├── Header/           # En-tête de l'application
│   └── TrackMap/         # Vue des voies ferroviaires
├── services/
│   └── smartYardApi.js   # Service API mocké pour les données
├── assets/               # Ressources statiques
├── App.jsx               # Composant principal
├── main.jsx              # Point d'entrée
└── index.css             # Styles globaux
```

## 🛠️ Installation

1. Cloner le repository :
```bash
git clone https://github.com/MildlyKeen/Projet-Innov-Siana.git
cd Projet-Innov-Siana
```

2. Installer les dépendances :
```bash
npm install
```

## 💻 Commandes Disponibles

### Développement
```bash
npm run dev
```
Lance le serveur de développement sur `http://localhost:5173`

### Build Production
```bash
npm run build
```
Crée une version optimisée pour la production dans le dossier `dist/`

### Preview Production
```bash
npm run preview
```
Prévisualise le build de production localement

### Linting
```bash
npm run lint
```
Vérifie la qualité du code avec ESLint

## 📱 Design Responsive

L'application est entièrement responsive et optimisée pour :

- 🖥️ **Desktop** - Affichage complet avec tous les graphiques
- 📱 **Tablette** - Layout adapté pour écrans moyens (768px et plus)
- 📱 **Mobile** - Interface optimisée pour smartphones (375px et plus)

## 🎨 Fonctionnalités

### Dashboard
- 4 cartes de statistiques principales
- Graphique linéaire du trafic ferroviaire (24h)
- Graphique circulaire de l'état des trains
- Graphique en barres de l'utilisation des voies

### Vue des Voies
- État en temps réel de chaque voie
- Indicateur visuel d'occupation
- Identification des trains présents
- Capacité actuelle vs maximale

### Mises à jour
- Rafraîchissement automatique des données toutes les 30 secondes
- Données mockées simulant un système réel

## 🔧 Configuration

Le projet utilise les outils suivants pour le développement :

- **ESLint** - Analyse statique du code
- **Vite** - Build tool ultra-rapide
- **React Plugin** - Support React avec Fast Refresh

## 📝 Notes de Développement

- Les données sont actuellement mockées via `src/services/smartYardApi.js`
- Pour connecter à une vraie API, modifier les fonctions dans `smartYardApi.js`
- Les graphiques utilisent Chart.js avec configuration responsive
- Bootstrap est utilisé pour le système de grille et les composants UI

## 🚀 Prochaines Étapes

- [ ] Connexion à une API backend réelle
- [ ] Authentification des utilisateurs
- [ ] Mode sombre
- [ ] Notifications en temps réel
- [ ] Export de données
- [ ] Historique des événements

## 📄 Licence

Ce projet est un MVP développé dans le cadre du projet Smart Yard.

## 👥 Contribution

Pour contribuer au projet, veuillez créer une branche et soumettre une pull request.

