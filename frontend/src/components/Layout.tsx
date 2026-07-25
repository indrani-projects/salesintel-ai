import { NavLink, Outlet } from "react-router-dom";
import {
  Building2,
  CalendarDays,
  LayoutGrid,
  Radar,
  Settings,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "../api/client";

type NavItem = {
  to: string;
  label: string;
  icon: LucideIcon;
  disabled?: boolean;
};

const navItems: NavItem[] = [
  { to: "/calendar", label: "Calendar", icon: CalendarDays },
  { to: "/dashboard", label: "Briefs", icon: LayoutGrid },
  { to: "/accounts", label: "Accounts", icon: Building2, disabled: true },
  { to: "/settings", label: "Settings", icon: Settings },
];

function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5 font-bold tracking-tight text-white">
      <span className="grid h-[26px] w-[26px] place-items-center rounded-lg bg-gradient-to-br from-brand-600 via-[#6d70ff] to-brand-600 text-white">
        <Radar className="h-4 w-4" />
      </span>
      <span className={compact ? "text-[15px]" : "text-[17px]"}>SalesIntel AI</span>
    </div>
  );
}

function NavRow({ item }: { item: NavItem }) {
  const { to, label, icon: Icon, disabled } = item;
  const base =
    "flex items-center gap-3 rounded-[9px] px-3 py-2.5 text-sm font-medium transition-colors";

  if (disabled) {
    return (
      <span
        className={`${base} cursor-default text-nav-ink/45`}
        aria-disabled="true"
        title="Coming soon"
      >
        <Icon className="h-[18px] w-[18px]" />
        {label}
      </span>
    );
  }
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `${base} ${
          isActive
            ? "bg-[rgba(109,112,255,0.16)] text-white"
            : "text-nav-ink hover:bg-white/5 hover:text-white"
        }`
      }
    >
      <Icon className="h-[18px] w-[18px]" />
      {label}
    </NavLink>
  );
}

function UserFooter({ online, configured }: { online: boolean; configured: boolean }) {
  return (
    <div className="border-t border-white/10 pt-3">
      <div className="mb-2 flex items-center gap-1.5 px-2 text-[11px] text-nav-ink/70">
        <span
          className={`h-1.5 w-1.5 rounded-full ${online ? "bg-good" : "bg-bad"}`}
        />
        Backend {online ? "connected" : "offline"}
        <span className="text-nav-ink/40">·</span>
        LLM {configured ? "on" : online ? "off" : "—"}
      </div>
      <div className="flex items-center gap-2.5 px-2 py-1 text-[13px] text-white">
        <span className="grid h-7 w-7 place-items-center rounded-full bg-brand-600 text-[12px] font-bold text-white">
          RM
        </span>
        <div className="leading-tight">
          Rohan M.
          <br />
          <span className="text-[11px] text-faint">Sales Representative</span>
        </div>
      </div>
    </div>
  );
}

export function Layout() {
  const { data: health, isError } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: false,
    refetchInterval: 15000,
  });

  const online = !isError && !!health;
  const configured = !!health?.llm_configured;

  return (
    <div className="min-h-screen min-[960px]:grid min-[960px]:grid-cols-[236px_1fr]">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen flex-col gap-1.5 bg-nav px-4 py-5 min-[960px]:flex">
        <div className="px-2 pb-4">
          <Logo />
        </div>
        <nav className="flex flex-col gap-1.5">
          {navItems.map((item) => (
            <NavRow key={item.to} item={item} />
          ))}
        </nav>
        <div className="flex-1" />
        <UserFooter online={online} configured={configured} />
      </aside>

      {/* Mobile top bar */}
      <header className="flex items-center justify-between gap-3 bg-nav px-4 py-3 min-[960px]:hidden">
        <Logo compact />
        <nav className="flex items-center gap-1">
          {navItems
            .filter((i) => !i.disabled)
            .map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-1.5 text-[13px] font-semibold transition-colors ${
                    isActive
                      ? "bg-[rgba(109,112,255,0.18)] text-white"
                      : "text-nav-ink hover:text-white"
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
        </nav>
      </header>

      {/* Main */}
      <main className="min-w-0 px-4 py-6 sm:px-7 sm:py-6">
        <div className="mx-auto w-full max-w-6xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
