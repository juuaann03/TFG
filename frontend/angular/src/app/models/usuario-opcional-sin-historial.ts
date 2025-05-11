export interface ConfiguracionPc {
    so?: string;
    procesador?: string;
    memoria?: string;
    tarjetaGrafica?: string;
  }
  
  export interface JuegoPoseido {
    nombre?: string;
    consolasDisponibles?: string[];
  }
  
  export interface UsuarioOpcionalSinHistorial {
    consolas?: string[];
    configuracionPc?: ConfiguracionPc;
    necesidadesEspeciales?: string[];
    juegosGustados?: string[];
    juegosNoGustados?: string[];
    juegosJugados?: string[];
    suscripciones?: string[];
    idiomas?: string[];
    juegosPoseidos?: JuegoPoseido[];
  }