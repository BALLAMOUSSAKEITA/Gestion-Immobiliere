import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col items-center justify-center gap-4 px-6 text-center">
      <p className="text-6xl font-bold text-zinc-300">404</p>
      <h1 className="text-2xl font-bold">Page introuvable</h1>
      <p className="text-zinc-600">La page demandée n&apos;existe pas ou a été déplacée.</p>
      <Link href="/" className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white">
        Retour à l&apos;accueil
      </Link>
    </main>
  );
}
