import { Component } from '@angular/core';
import { CommonModule } from '@angular/common'; // Añadir
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule], // Añadir CommonModule, quitar RouterLink
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss'
})
export class RegisterComponent {
  registerForm: FormGroup;
  error: string | null = null;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private router: Router
  ) {
    this.registerForm = this.fb.group({
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  submitRegister(): void {
    if (this.registerForm.valid) {
      const { name, email, password } = this.registerForm.value;
      this.apiService.post<any>('usuarios', { name, email, password }).subscribe({
        next: (response) => {
          this.router.navigate(['/dashboard']);
        },
        error: (err) => {
          this.error = 'Error al crear cuenta: ' + err.message;
        }
      });
    }
  }
}