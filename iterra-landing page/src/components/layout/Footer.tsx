import { Twitter, Linkedin, Github, Youtube } from "lucide-react";

const FOOTER_LINKS = {
  Product: [
    { label: "Features", href: "#features" },
    { label: "How it works", href: "#how-it-works" },
    { label: "Pricing", href: "#pricing" },
    { label: "Changelog", href: "#" },
    { label: "Roadmap", href: "#" },
  ],
  Company: [
    { label: "About", href: "#" },
    { label: "Blog", href: "#" },
    { label: "Careers", href: "#" },
    { label: "Press", href: "#" },
    { label: "Contact", href: "#" },
  ],
  Legal: [
    { label: "Privacy", href: "#" },
    { label: "Terms", href: "#" },
    { label: "Cookies", href: "#" },
    { label: "Security", href: "#" },
  ],
};

const SOCIAL_LINKS = [
  { icon: Twitter, label: "Twitter", href: "#" },
  { icon: Linkedin, label: "LinkedIn", href: "#" },
  { icon: Github, label: "GitHub", href: "#" },
  { icon: Youtube, label: "YouTube", href: "#" },
];

export default function Footer() {
  return (
    <footer className="border-t border-white/[0.05]">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-10 lg:gap-12">
          {/* Brand */}
          <div className="col-span-2">
            <a href="/" className="flex items-center gap-2.5 mb-4">
              <svg width="20" height="20" viewBox="0 0 22 22" fill="none" aria-hidden="true">
                <path
                  d="M11 2L13.5 8.5L20 11L13.5 13.5L11 20L8.5 13.5L2 11L8.5 8.5L11 2Z"
                  fill="url(#footer-logo-grad)"
                />
                <defs>
                  <linearGradient id="footer-logo-grad" x1="2" y1="2" x2="20" y2="20" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#a78bfa" />
                    <stop offset="1" stopColor="#7c5cfc" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="text-[15px] font-semibold tracking-tight text-white/80">Ittera</span>
            </a>
            <p className="text-[13px] text-white/28 leading-[1.75] max-w-xs mb-6">
              The AI content strategy engine for creators, founders, and marketers who play to win.
            </p>
            <div className="flex items-center gap-2.5">
              {SOCIAL_LINKS.map(({ icon: Icon, label, href }) => (
                <a
                  key={label}
                  href={href}
                  aria-label={label}
                  className="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-white/28 hover:text-white/60 hover:bg-white/[0.07] transition-all duration-200"
                >
                  <Icon className="w-3.5 h-3.5" />
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          {Object.entries(FOOTER_LINKS).map(([category, links]) => (
            <div key={category}>
              <h3 className="text-[12px] font-semibold text-white/40 mb-4 tracking-wide uppercase">
                {category}
              </h3>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-[13px] text-white/28 hover:text-white/55 transition-colors duration-200"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 pt-7 border-t border-white/[0.05] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <p className="text-[12px] text-white/18">
            © {new Date().getFullYear()} Ittera, Inc. All rights reserved.
          </p>
          <p className="text-[12px] text-white/14">
            Built for creators who compound.
          </p>
        </div>
      </div>
    </footer>
  );
}
