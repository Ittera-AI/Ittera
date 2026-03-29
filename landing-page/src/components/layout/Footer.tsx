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
    <footer className="bg-[#F9F8F6] border-t border-[#EAEAEC]">
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
                    <stop stopColor="#0F172A" />
                    <stop offset="1" stopColor="#A38A70" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="text-[15px] font-semibold tracking-tight text-neutral-800">Ittera</span>
            </a>
            <p className="text-[13px] text-neutral-500 leading-[1.75] max-w-xs mb-6">
              The AI content strategy engine for creators, founders, and marketers who play to win.
            </p>
            <div className="flex items-center gap-2.5">
              {SOCIAL_LINKS.map(({ icon: Icon, label, href }) => (
                <a
                  key={label}
                  href={href}
                  aria-label={label}
                  className="w-8 h-8 rounded-lg bg-white border border-[#EAEAEC] flex items-center justify-center text-neutral-500 hover:text-neutral-800 hover:bg-[#F5F5F4] hover:border-[#D4D4D4] transition-all duration-300"
                >
                  <Icon className="w-3.5 h-3.5" />
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          {Object.entries(FOOTER_LINKS).map(([category, links]) => (
            <div key={category}>
              <h3 className="text-[12px] font-semibold text-neutral-400 mb-4 tracking-wide uppercase">
                {category}
              </h3>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-[13px] text-neutral-400 hover:text-neutral-700 transition-all duration-300"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 pt-7 border-t border-[#EAEAEC] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <p className="text-[12px] text-neutral-300">
            © {new Date().getFullYear()} Ittera, Inc. All rights reserved.
          </p>
          <p className="text-[12px] text-neutral-200">
            Built for creators who compound.
          </p>
        </div>
      </div>
    </footer>
  );
}
