import React from 'react';
import './Header.css';

const Header = () => {
  return (
    <header className="smart-yard-header">
      <div className="container-fluid">
        <div className="row align-items-center py-3">
          <div className="col-12 col-md-6">
            <h1 className="h3 mb-0 text-white">🚂 Smart Yard</h1>
            <p className="text-white-50 mb-0 small">Système de Gestion Ferroviaire</p>
          </div>
          <div className="col-12 col-md-6 text-md-end mt-2 mt-md-0">
            <span className="badge bg-success me-2">Système Actif</span>
            <span className="text-white-50 small">{new Date().toLocaleDateString('fr-FR')}</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
