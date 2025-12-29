import React from 'react';
import './Header.css';
import reactLogo from '../../assets/react.svg';
import headerBg from '../../assets/train.png';
import siteLogo from '../../assets/train logo.png';

const Header = () => {
  // Prefer assets bundled in src/assets; fall back to public path or bundled react.svg
  const publicLogoPath = '/assets/logo.png';
  const logoSrc = siteLogo || publicLogoPath;

  const handleImgError = (e) => {
    e.currentTarget.onerror = null;
    e.currentTarget.src = reactLogo;
  };

  return (
    <header className="smart-yard-header">
      <div
        className="header-bg-overlay"
        aria-hidden="true"
        style={{ backgroundImage: `url(${headerBg})` }}
      />
      <div className="container-fluid">
        <div className="row align-items-center py-3">
          <div className="col-12 col-md-6 d-flex align-items-center gap-3">
            <img
              src={logoSrc}
              alt="Smart Yard logo"
              className="site-logo"
              onError={handleImgError}
            />
            <div>
              <h1 className="h3 mb-0 text-white">Smart Yard - Supervision</h1>
              <p className="text-white-50 mb-0 small">Système de Gestion Ferroviaire</p>
            </div>
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
