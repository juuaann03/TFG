import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { ProximoLanzamiento } from '../models/proximo-lanzamiento';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class LanzamientosService {
  private baseUrl = environment.apiUrl; // 'http://localhost:8000'
  private proximosLanzamientos: ProximoLanzamiento[] | null = null; // Caché en memoria

  constructor(private http: HttpClient) {}

  getProximosLanzamientos(correo: string): Observable<ProximoLanzamiento[]> {
    // Si ya tenemos los datos en caché, devolverlos sin hacer la llamada
    if (this.proximosLanzamientos) {
      return of(this.proximosLanzamientos);
    }

    // Hacer la llamada al endpoint y almacenar los datos en caché
    return this.http.get<ProximoLanzamiento[]>(`${this.baseUrl}/lanzamientos/proximos/${correo}`).pipe(
      map(response => response.map(juego => ({
        titulo: juego.titulo || 'Juego desconocido',
        imagen: juego.imagen || 'https://via.placeholder.com/150',
        plataformas: juego.plataformas || 'Desconocido',
        fecha_lanzamiento: juego.fecha_lanzamiento || 'Desconocido'
      }))),
      tap(lanzamientos => {
        this.proximosLanzamientos = lanzamientos; // Guardar en caché
      }),
      catchError(err => {
        console.error('Error al cargar próximos lanzamientos:', err);
        return of([]); // Devolver array vacío en caso de error
      })
    );
  }

  // Método para limpiar el caché (opcional, por si quieres forzar una recarga)
  clearCache(): void {
    this.proximosLanzamientos = null;
  }
}