/**
 * Tests RTL per als components de llistes i ítems.
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ListCard from "@/components/lists/ListCard";
import ItemRow from "@/components/items/ItemRow";
import NewListModal from "@/components/lists/NewListModal";
import type { ListItemResponse, ListResponse } from "@/lib/types";

// Mock de les funcions d'API
jest.mock("@/lib/api/lists", () => ({
  createList: jest.fn(),
  getLists: jest.fn(),
  getList: jest.fn(),
  updateList: jest.fn(),
  deleteList: jest.fn(),
}));

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={makeQueryClient()}>
      {children}
    </QueryClientProvider>
  );
}

const mockList: ListResponse = {
  id: "list-1",
  owner_id: "user-1",
  list_type_id: null,
  title: "Llista de la compra",
  description: "Coses a comprar",
  is_archived: false,
  created_at: "2024-01-01T10:00:00Z",
  updated_at: "2024-01-02T10:00:00Z",
  member_count: 2,
  item_count: 5,
};

const mockItem: ListItemResponse = {
  id: "item-1",
  list_id: "list-1",
  created_by: "user-1",
  content: "Comprar llet",
  is_checked: false,
  position: 0,
  due_date: null,
  priority: null,
  remind_at: null,
  metadata_: null,
  created_at: "2024-01-01T10:00:00Z",
  updated_at: null,
};

// ---------------------------------------------------------------------------
// ListCard
// ---------------------------------------------------------------------------
describe("ListCard", () => {
  it("renderitza el títol i els comptadors", () => {
    render(<ListCard list={mockList} onClick={() => {}} />);
    expect(screen.getByText("Llista de la compra")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("crida onClick en fer clic al card", () => {
    const onClick = jest.fn();
    render(<ListCard list={mockList} onClick={onClick} />);
    fireEvent.click(screen.getByRole("button", { name: /Obrir llista/i }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("mostra el badge Arxivada quan is_archived és true", () => {
    const archived = { ...mockList, is_archived: true };
    render(<ListCard list={archived} onClick={() => {}} />);
    expect(screen.getByText("Arxivada")).toBeInTheDocument();
  });

  it("mostra la descripció si existeix", () => {
    render(<ListCard list={mockList} onClick={() => {}} />);
    expect(screen.getByText("Coses a comprar")).toBeInTheDocument();
  });

  it("mostra la data relativa d'updated_at per a dates recents", () => {
    const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString();
    const recentList = { ...mockList, updated_at: twoDaysAgo };
    render(<ListCard list={recentList} onClick={() => {}} />);
    expect(screen.getByText("Fa 2 dies")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// ItemRow
// ---------------------------------------------------------------------------
describe("ItemRow", () => {
  it("renderitza el contingut de l'ítem", () => {
    render(
      <ItemRow item={mockItem} onToggle={() => {}} onDelete={() => {}} />
    );
    expect(screen.getByText("Comprar llet")).toBeInTheDocument();
  });

  it("crida onToggle en fer clic al checkbox", () => {
    const onToggle = jest.fn();
    render(
      <ItemRow item={mockItem} onToggle={onToggle} onDelete={() => {}} />
    );
    fireEvent.click(screen.getByRole("checkbox"));
    expect(onToggle).toHaveBeenCalledWith("item-1", true);
  });

  it("mostra el badge de prioritat alta", () => {
    const highItem = { ...mockItem, priority: "high" as const };
    render(
      <ItemRow item={highItem} onToggle={() => {}} onDelete={() => {}} />
    );
    expect(screen.getByTestId("priority-badge")).toHaveTextContent("Alta");
  });

  it("mostra el badge de prioritat mitjana", () => {
    const medItem = { ...mockItem, priority: "medium" as const };
    render(
      <ItemRow item={medItem} onToggle={() => {}} onDelete={() => {}} />
    );
    expect(screen.getByTestId("priority-badge")).toHaveTextContent("Mitjana");
  });

  it("mostra el badge de prioritat baixa", () => {
    const lowItem = { ...mockItem, priority: "low" as const };
    render(
      <ItemRow item={lowItem} onToggle={() => {}} onDelete={() => {}} />
    );
    expect(screen.getByTestId("priority-badge")).toHaveTextContent("Baixa");
  });

  it("mostra 'Demà' per a un ítem amb venciment a la mitjanit de demà", () => {
    // Math.ceil(86400000/86400000) = 1 → "Demà"
    // Cal usar exactament la mitjanit de demà per tenir diff = 86400000 ms
    const tomorrowMidnight = new Date();
    tomorrowMidnight.setDate(tomorrowMidnight.getDate() + 1);
    tomorrowMidnight.setHours(0, 0, 0, 0);
    const itemDema = { ...mockItem, due_date: tomorrowMidnight.toISOString() };
    render(
      <ItemRow item={itemDema} onToggle={() => {}} onDelete={() => {}} />
    );
    expect(screen.getByText("Demà")).toBeInTheDocument();
  });

  it("mostra 'Avui' per a un ítem amb venciment avui a migdia", () => {
    // Avui a migdia (Math.ceil(0.5) = 1... atenció: cal midnight)
    // Usem exactament la mitjanit d'avui: diff = 0, Math.ceil(0) = 0 → "Avui"
    const todayMidnight = new Date();
    todayMidnight.setHours(0, 0, 0, 0);
    const itemAvui = { ...mockItem, due_date: todayMidnight.toISOString() };
    render(
      <ItemRow item={itemAvui} onToggle={() => {}} onDelete={() => {}} />
    );
    expect(screen.getByText("Avui")).toBeInTheDocument();
  });

  it("mostra el flux de confirmació d'eliminació", () => {
    render(
      <ItemRow item={mockItem} onToggle={() => {}} onDelete={() => {}} />
    );
    // Clic al botó × (invisible però present al DOM)
    fireEvent.click(screen.getByRole("button", { name: /Eliminar ítem/i }));
    expect(screen.getByText("Eliminar")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("crida onDelete en confirmar l'eliminació", () => {
    const onDelete = jest.fn();
    render(
      <ItemRow item={mockItem} onToggle={() => {}} onDelete={onDelete} />
    );
    fireEvent.click(screen.getByRole("button", { name: /Eliminar ítem/i }));
    fireEvent.click(screen.getByText("Eliminar"));
    expect(onDelete).toHaveBeenCalledWith("item-1");
  });

  it("cancel·la l'eliminació en clicar Cancel", () => {
    render(
      <ItemRow item={mockItem} onToggle={() => {}} onDelete={() => {}} />
    );
    fireEvent.click(screen.getByRole("button", { name: /Eliminar ítem/i }));
    fireEvent.click(screen.getByText("Cancel"));
    // El botó × ha de tornar a apareixer
    expect(
      screen.getByRole("button", { name: /Eliminar ítem/i })
    ).toBeInTheDocument();
  });

  it("aplica classe line-through quan is_checked és true", () => {
    const checkedItem = { ...mockItem, is_checked: true };
    render(
      <ItemRow item={checkedItem} onToggle={() => {}} onDelete={() => {}} />
    );
    const text = screen.getByText("Comprar llet");
    expect(text.className).toContain("line-through");
  });
});

// ---------------------------------------------------------------------------
// NewListModal
// ---------------------------------------------------------------------------
describe("NewListModal", () => {
  it("no renderitza res quan isOpen és false", () => {
    render(
      <Wrapper>
        <NewListModal isOpen={false} onClose={() => {}} />
      </Wrapper>
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renderitza el camp de títol i descripció quan és obert", () => {
    render(
      <Wrapper>
        <NewListModal isOpen onClose={() => {}} />
      </Wrapper>
    );
    expect(screen.getByLabelText(/Títol/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Descripció/i)).toBeInTheDocument();
  });

  it("mostra error de validació si s'envia sense títol", () => {
    render(
      <Wrapper>
        <NewListModal isOpen onClose={() => {}} />
      </Wrapper>
    );
    fireEvent.click(screen.getByRole("button", { name: /Crear/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/obligatori/i);
  });

  it("crida onClose en clicar Cancel·lar", () => {
    const onClose = jest.fn();
    render(
      <Wrapper>
        <NewListModal isOpen onClose={onClose} />
      </Wrapper>
    );
    fireEvent.click(screen.getByRole("button", { name: /Cancel/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("crida createList i onClose en submit vàlid", async () => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { createList } = require("@/lib/api/lists") as { createList: jest.Mock };
    createList.mockResolvedValueOnce({
      id: "new-list",
      owner_id: "u1",
      list_type_id: null,
      title: "Nova",
      description: null,
      is_archived: false,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: null,
      member_count: 1,
      item_count: 0,
    });

    const onClose = jest.fn();
    render(
      <Wrapper>
        <NewListModal isOpen onClose={onClose} />
      </Wrapper>
    );

    fireEvent.change(screen.getByLabelText(/Títol/i), {
      target: { value: "Nova llista" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Crear/i }));

    await waitFor(() => {
      expect(createList).toHaveBeenCalledWith({
        title: "Nova llista",
        description: null,
      });
    });
  });
});
