import { Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';
import { LoginComponent } from './components/login/login.component';
import { RegisterComponent } from './components/register/register.component';
import { PrincipalComponent } from './components/principal/principal.component';
import { AjustesCuentaComponent } from './components/ajustes-cuenta/ajustes-cuenta.component'; // Asegúrate de que exista

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  { path: 'principal', component: PrincipalComponent },
  { path: 'ajustes-cuenta', component: AjustesCuentaComponent },
  { path: 'dashboard', redirectTo: '' },
  { path: '**', redirectTo: '' }
];