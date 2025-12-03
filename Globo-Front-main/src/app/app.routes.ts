import { Routes } from '@angular/router';
import { MonitorComponent } from './pages/monitor/monitor';
import { DashboardComponent } from './pages/dashboard/dashboard';
import { HistoryComponent } from './pages/history/history';

export const routes: Routes = [
  { path: '', redirectTo: 'monitor', pathMatch: 'full' },
  { path: 'monitor', component: MonitorComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'historico', component: HistoryComponent }
];