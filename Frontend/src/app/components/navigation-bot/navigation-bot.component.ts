import { Component, AfterViewInit, ElementRef, ViewChildren, QueryList, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import * as L from 'leaflet';

@Component({
  selector: 'app-navigation-bot',
  templateUrl: './navigation-bot.component.html',
  styleUrls: ['./navigation-bot.component.css']
})
export class NavigationBotComponent implements AfterViewInit, OnInit { // Add OnInit
  userMessage: string = '';
  messages: { sender: string; text: string; location?: { lat: number; lng: number; title: string }; mapId?: string }[] = [];
  private defaultApiUrl = '/api/navigation-bot'; // Valeur par défaut

  @ViewChildren('mapContainer') mapContainers!: QueryList<ElementRef>; // Référence aux conteneurs de cartes

  private maps: { [key: string]: L.Map } = {}; // Stocke les instances des cartes Leaflet
  private markers: { [key: string]: L.Marker } = {}; // Stocke les marqueurs

  constructor(private http: HttpClient) {}

  ngOnInit() {
    // Ajouter un message de bienvenue en français lors de l'initialisation
    this.messages.push({
      sender: 'bot',
      text: "Hello! I'm your campus assistant. How can I help you today ?"
    });
  }

  ngAfterViewInit() {
    // Initialiser les cartes après que les messages soient rendus
    this.mapContainers.changes.subscribe(() => {
      this.initMaps();
    });
  }

  private initMaps() {
    this.messages.forEach((message, index) => {
      if (message.mapId && message.location) {
        const mapId = message.mapId;
        const mapElement = document.getElementById(mapId);

        if (mapElement && !this.maps[mapId]) {
          this.maps[mapId] = L.map(mapElement, {
            zoomControl: true, // Ajout du contrôle de zoom
            scrollWheelZoom: false // Désactivation du zoom par molette
          }).setView([message.location.lat, message.location.lng], 15);

          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          }).addTo(this.maps[mapId]);

          this.markers[mapId] = L.marker([message.location.lat, message.location.lng], {
            icon: L.icon({
              iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
              iconSize: [25, 41],
              iconAnchor: [12, 41],
              popupAnchor: [1, -34]
            })
          })
            .addTo(this.maps[mapId])
            .bindPopup(message.location.title)
            .openPopup();
        }
      }
    });
  }

  private get apiUrl(): string {
    return (window as any).__env?.navigationBotApiUrl || this.defaultApiUrl;
  }

  sendMessage() {
    if (!this.userMessage.trim()) return;

    this.messages.push({ sender: 'user', text: this.userMessage });

    this.http.post<{ answer: string; source: any }>(`${this.apiUrl}/ask`, { query: this.userMessage }).subscribe({
      next: (response) => {
        console.log(this.apiUrl);
        console.log('Response from backend:', response);

        if (response.source && response.source.lat && response.source.lng) {
          const mapId = `map-${this.messages.length}`; // Identifiant unique pour chaque carte
          this.messages.push({
            sender: 'bot',
            text: response.answer,
            location: {
              lat: response.source.lat,
              lng: response.source.lng,
              title: response.source.title
            },
            mapId: mapId
          });
        } else {
          this.messages.push({ sender: 'bot', text: response.answer });
        }

        setTimeout(() => {
          this.initMaps();
        }, 0);
      },
      error: (error) => {
        console.error('Error:', error);
        this.messages.push({ sender: 'bot', text: 'Désolé, une erreur s’est produite. Veuillez réessayer.' });
      }
    });

    this.userMessage = '';
  }
}
