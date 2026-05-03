import { useQuery } from "@tanstack/react-query";
import { get } from "@/lib/api/client";

export interface ListTypeDto {
  id: string;
  slug: string;
  label: string;
  icon: string | null;
}

export function useListTypes() {
  return useQuery({
    queryKey: ["list-types"],
    queryFn: async () => get<ListTypeDto[]>("/api/v1/list-types/"),
    staleTime: 1000 * 60 * 60,
  });
}
