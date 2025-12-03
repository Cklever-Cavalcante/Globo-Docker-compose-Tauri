import { Injectable } from '@angular/core';
import { invoke } from '@tauri-apps/api/core';

@Injectable({
    providedIn: 'root'
})
export class DockerService {

    constructor() { }

    async startServices(): Promise<string> {
        try {
            return await invoke<string>('start_services');
        } catch (error) {
            console.error('Error starting services:', error);
            throw error;
        }
    }

    async stopServices(): Promise<string> {
        try {
            return await invoke<string>('stop_services');
        } catch (error) {
            console.error('Error stopping services:', error);
            throw error;
        }
    }

    async checkStatus(): Promise<string> {
        try {
            return await invoke<string>('check_status');
        } catch (error) {
            console.error('Error checking status:', error);
            throw error;
        }
    }
}
