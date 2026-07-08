import { Phone } from "lucide-react";
import { siteContent } from "../data/siteContent";

export function Header() {
  const { assets, header, site } = siteContent;

  return (
    <header className="site-header">
      <a className="brand" href="#top" aria-label={header.homeAriaLabel}>
        <img src={assets.logo} alt={header.logoAlt} />
      </a>
      <nav className="site-nav" aria-label={header.navAriaLabel}>
        {header.navItems.map((item) => (
          <a key={item.href} href={item.href}>
            {item.label}
          </a>
        ))}
      </nav>
      <a className="header-call" href={site.phoneHref}>
        <Phone size={18} aria-hidden="true" />
        <span>{header.bookingLabel}</span>
      </a>
    </header>
  );
}
