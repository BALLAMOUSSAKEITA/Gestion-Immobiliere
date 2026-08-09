"use client";

import Link from "next/link";
import { Bell } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchNotifications,
  fetchUnreadNotificationCount,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { cn } from "@/lib/utils";
import { useConfirm } from "@/contexts/confirm-context";
import { modifyConfirm } from "@/lib/confirm-presets";

type NotificationBellProps = {
  notificationsPath?: string;
};

export function NotificationBell({
  notificationsPath = "/dashboard/notifications",
}: NotificationBellProps) {
  const confirm = useConfirm();
  const [count, setCount] = useState(0);
  const [items, setItems] = useState<NotificationSummary[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const [countData, listData] = await Promise.all([
      fetchUnreadNotificationCount(token),
      fetchNotifications(token, 10),
    ]);
    setCount(countData.count);
    setItems(listData.items);
  }, []);

  useEffect(() => {
    load().catch(() => undefined);
    const interval = setInterval(() => {
      load().catch(() => undefined);
    }, 30000);
    return () => clearInterval(interval);
  }, [load]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleMarkRead(id: string) {
    const token = getAccessToken();
    if (!token) return;
    if (!(await confirm(modifyConfirm("Marquer cette notification comme lue ?")))) return;
    try {
      await markNotificationRead(token, id);
      await load();
    } catch (err) {
      if (err instanceof ApiError) return;
    }
  }

  async function handleMarkAllRead() {
    const token = getAccessToken();
    if (!token) return;
    if (!(await confirm(modifyConfirm("Marquer toutes les notifications comme lues ?")))) return;
    await markAllNotificationsRead(token);
    await load();
  }

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        aria-label="Notifications"
        onClick={() => setOpen((value) => !value)}
        className="relative flex h-10 w-10 items-center justify-center rounded-full bg-faint text-foreground transition-colors hover:bg-[var(--bebe)]"
      >
        <Bell className="h-4 w-4" />
        {count > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-destructive px-1 text-xs font-bold text-white">
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-[12px] bg-card shadow-[var(--shadow-dropdown)]">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <p className="font-semibold">Notifications</p>
            {count > 0 && (
              <button
                type="button"
                className="text-xs text-accent hover:underline"
                onClick={handleMarkAllRead}
              >
                Tout marquer lu
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {items.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-muted-foreground">
                Aucune notification
              </p>
            ) : (
              items.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleMarkRead(item.id)}
                  className={cn(
                    "block w-full border-b border-border px-4 py-3 text-left transition-colors hover:bg-muted/50",
                    !item.is_read && "bg-secondary/50",
                  )}
                >
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{item.body}</p>
                </button>
              ))
            )}
          </div>
          <div className="border-t border-border px-4 py-3">
            <Button asChild variant="outline" className="w-full">
              <Link href={notificationsPath} onClick={() => setOpen(false)}>
                Voir tout
              </Link>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
