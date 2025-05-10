export interface Recomendacion {
  nombre: string;
  imagen?: string;
  genero?: string;
  plataformas?: string;
  razon?: string;
}

export interface JuegoFuturo {
  nombre: string;
  imagen?: string;
  fecha_lanzamiento?: string;
  plataformas?: string;
}