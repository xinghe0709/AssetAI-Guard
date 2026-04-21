function AuthLayout({ leftContent, rightContent, footer }) {
    return (
      <div className="auth-page">
        <div className="auth-main">
          <section className="auth-left">
            {leftContent}
          </section>
  
          <section className="auth-right">
            {rightContent}
          </section>
        </div>
  
        {footer && <footer className="auth-footer">{footer}</footer>}
      </div>
    );
  }
  
  export default AuthLayout;