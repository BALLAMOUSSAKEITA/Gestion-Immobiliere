export type NavItem = {
  href: string;
  label: string;
  roles: string[];
};

export type NavGroup = {
  title: string;
  items: NavItem[];
};

export const DASHBOARD_NAV: NavGroup[] = [
  {
    title: "Principal",
    items: [{ href: "/dashboard", label: "Tableau de bord", roles: ["all"] }],
  },
  {
    title: "Patrimoine",
    items: [
      { href: "/dashboard/immeubles", label: "Immeubles", roles: ["super_admin", "admin_familial", "proprietaire", "gestionnaire"] },
      { href: "/dashboard/logements", label: "Logements", roles: ["super_admin", "admin_familial", "proprietaire", "gestionnaire"] },
    ],
  },
  {
    title: "Locataires",
    items: [
      { href: "/dashboard/locataires", label: "Locataires", roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire"] },
      { href: "/dashboard/baux", label: "Baux", roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire"] },
    ],
  },
  {
    title: "Finances",
    items: [
      { href: "/dashboard/paiements", label: "Paiements", roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire", "locataire"] },
      { href: "/dashboard/impayes", label: "Impayés", roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire"] },
      { href: "/dashboard/relances", label: "Relances", roles: ["super_admin", "admin_familial", "gestionnaire"] },
      { href: "/dashboard/recus", label: "Reçus", roles: ["super_admin", "admin_familial", "gestionnaire", "locataire"] },
      { href: "/dashboard/depenses", label: "Dépenses", roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire"] },
    ],
  },
  {
    title: "Opérations",
    items: [
      { href: "/dashboard/reparations", label: "Réparations", roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire", "locataire"] },
      { href: "/dashboard/documents", label: "Documents", roles: ["super_admin", "admin_familial", "gestionnaire", "proprietaire", "locataire"] },
      { href: "/dashboard/demandes-visite", label: "Visites", roles: ["super_admin", "admin_familial", "gestionnaire"] },
    ],
  },
  {
    title: "Administration",
    items: [
      { href: "/dashboard/validations", label: "Validations", roles: ["super_admin"] },
      { href: "/dashboard/mes-demandes", label: "Mes demandes", roles: ["super_admin", "admin_familial", "gestionnaire"] },
      { href: "/dashboard/historique", label: "Historique", roles: ["super_admin", "admin_familial"] },
      { href: "/dashboard/rapports", label: "Rapports", roles: ["super_admin", "admin_familial", "proprietaire"] },
      { href: "/dashboard/utilisateurs", label: "Utilisateurs", roles: ["super_admin"] },
      { href: "/dashboard/proprietaires", label: "Propriétaires", roles: ["super_admin", "admin_familial"] },
      { href: "/dashboard/notifications", label: "Notifications", roles: ["all"] },
      { href: "/dashboard/parametres/notifications", label: "Préférences", roles: ["all"] },
    ],
  },
];

export const TENANT_NAV = [
  { href: "/espace-locataire", label: "Tableau de bord" },
  { href: "/espace-locataire/mon-logement", label: "Mon logement" },
  { href: "/espace-locataire/mon-contrat", label: "Mon contrat" },
  { href: "/espace-locataire/paiements", label: "Paiements" },
  { href: "/espace-locataire/recus", label: "Reçus" },
  { href: "/espace-locataire/impayes", label: "Impayés" },
  { href: "/espace-locataire/reparations", label: "Réparations" },
  { href: "/espace-locataire/documents", label: "Documents" },
  { href: "/espace-locataire/messages", label: "Messages" },
  { href: "/espace-locataire/notifications", label: "Notifications" },
];

export const PUBLIC_NAV = [
  { href: "/annonces", label: "Annonces" },
  { href: "/contact", label: "Contact" },
];

export function filterDashboardNav(roleCode: string): NavGroup[] {
  return DASHBOARD_NAV.map((group) => ({
    ...group,
    items: group.items.filter(
      (item) => item.roles.includes("all") || item.roles.includes(roleCode),
    ),
  })).filter((group) => group.items.length > 0);
}
