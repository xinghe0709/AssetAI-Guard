import React from "react";
import "../../styles/modal.css";

function Modal({ isOpen, title, subtitle, onClose, children, size = "medium" }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className={`modal-content modal-${size}`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        {title && (
          <div className="modal-header">
            <div className="modal-header-content">
              <h2 className="modal-title">{title}</h2>
              {subtitle && <p className="modal-subtitle">{subtitle}</p>}
            </div>
            <button className="modal-close-btn" onClick={onClose}>
              ✕
            </button>
          </div>
        )}

        {/* Modal Body */}
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

export default Modal;
