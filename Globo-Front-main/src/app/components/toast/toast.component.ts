import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="fixed top-6 right-6 z-[10000] flex flex-col gap-3 pointer-events-none">
      <div *ngFor="let toast of toastService.toasts()" 
           class="pointer-events-auto relative overflow-hidden min-w-[320px] bg-[#1E1E1E] border-l-4 text-white rounded shadow-2xl animate-slide-in flex items-center gap-4 p-4 backdrop-blur-md bg-opacity-95 border border-white/10"
           [ngClass]="{
             'border-l-green-500': toast.type === 'success',
             'border-l-red-500': toast.type === 'error',
             'border-l-blue-500': toast.type === 'info'
           }">
        
        <div [ngSwitch]="toast.type" class="shrink-0">
          <i *ngSwitchCase="'success'" class="fas fa-check-circle text-green-500 text-xl"></i>
          <i *ngSwitchCase="'error'" class="fas fa-exclamation-circle text-red-500 text-xl"></i>
          <i *ngSwitchCase="'info'" class="fas fa-info-circle text-blue-500 text-xl"></i>
        </div>
        
        <div class="flex-1 min-w-0">
          <h4 class="font-bold text-[10px] uppercase tracking-widest text-gray-400 mb-0.5">{{ toast.type }}</h4>
          <p class="text-sm font-medium leading-tight break-words">{{ toast.message }}</p>
        </div>

        <button (click)="toastService.remove(toast.id)" class="text-gray-500 hover:text-white transition-colors p-1">
          <i class="fas fa-times"></i>
        </button>

        <div class="absolute bottom-0 left-0 h-[3px] animate-progress"
             [ngClass]="{
               'bg-green-500': toast.type === 'success',
               'bg-red-500': toast.type === 'error',
               'bg-blue-500': toast.type === 'info'
             }">
        </div>

      </div>
    </div>
  `,
  styles: [`
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes progress {
      from { width: 100%; }
      to { width: 0%; }
    }

    .animate-slide-in { 
      animation: slideIn 0.4s cubic-bezier(0.2, 0.8, 0.2, 1); 
    }
    
    .animate-progress {
      animation: progress 3s linear forwards; /* 3s deve bater com o setTimeout do service */
    }
  `]
})
export class ToastComponent {
  constructor(public toastService: ToastService) {}
}