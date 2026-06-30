import { Phone } from "lucide-react";
import logo from "../assets/images/logo.png";

const navItems = [
  { label: "房型", href: "#rooms" },
  { label: "服務", href: "#services" },
  { label: "附近景點", href: "#nearby" },
  { label: "交通", href: "#traffic" },
];

export function Header() {
  return (
    <header className="site-header">
      <a className="brand" href="#top" aria-label="回到首頁">
        <img src={logo} alt="" />
        <span>富莉庭緣民宿</span>
      </a>
      <nav className="site-nav" aria-label="主要導覽">
        {navItems.map((item) => (
          <a key={item.href} href={item.href}>
            {item.label}
          </a>
        ))}
      </nav>
      <a className="header-call" href="tel:0932929748">
        <Phone size={18} aria-hidden="true" />
        <span>訂房</span>
      </a>
    </header>
  );
}
