export interface Recomendacion {
  nombre: string;
  imagen?: string;
  genero?: string;
  plataformas?: string;
  razon?: string;
  tiendas?: { nombre: string; slug: string; url: string; icono: string }[];
}