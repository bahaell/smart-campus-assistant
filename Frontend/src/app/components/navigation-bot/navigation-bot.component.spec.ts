import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { NavigationBotComponent } from './navigation-bot.component';
import { LucideAngularModule } from 'lucide-angular';
import { Send } from 'lucide-angular';
import * as L from 'leaflet';

describe('NavigationBotComponent', () => {
  let component: NavigationBotComponent;
  let fixture: ComponentFixture<NavigationBotComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    // Simuler process.env pour les tests
    (process.env as any) = {
      NG_APP_API_URL: 'http://navigation-bot:8001'
    };

    await TestBed.configureTestingModule({
      declarations: [NavigationBotComponent],
      imports: [
        HttpClientTestingModule,
        FormsModule,
        LucideAngularModule.pick({ Send })
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(NavigationBotComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should add welcome message on initialization', () => {
    expect(component.messages.length).toBe(1);
    expect(component.messages[0]).toEqual({
      sender: 'bot',
      text: 'Bonjour ! Je suis votre assistant campus. Comment puis-je vous aider aujourd’hui ?'
    });
  });

  it('should call API and add bot response with location to messages array', fakeAsync(() => {
    component.userMessage = 'Où se trouve le Bloc Prepa ?';
    component.sendMessage();

    const req = httpMock.expectOne('http://navigation-bot:8001/ask');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ query: 'Où se trouve le Bloc Prepa ?' });

    req.flush({
      answer: "L'emplacement 'Bloc Prepa' se trouve ici :",
      source: {
        type: 'location',
        title: 'Bloc Prepa',
        lat: 36.8344411,
        lng: 10.1456052,
        distance: 0.123456
      }
    });

    tick();

    expect(component.messages.length).toBe(3);
    expect(component.messages[2]).toEqual({
      sender: 'bot',
      text: "L'emplacement 'Bloc Prepa' se trouve ici :",
      location: {
        lat: 36.8344411,
        lng: 10.1456052,
        title: 'Bloc Prepa'
      },
      mapId: 'map-2'
    });
  }));

  it('should handle API error and add error message to messages array', () => {
    component.userMessage = 'Où se trouve le Bloc Prepa ?';
    component.sendMessage();

    const req = httpMock.expectOne('http://navigation-bot:8001/ask');
    req.flush('Error', { status: 500, statusText: 'Server Error' });

    expect(component.messages.length).toBe(3);
    expect(component.messages[2]).toEqual({
      sender: 'bot',
      text: 'Désolé, une erreur s’est produite. Veuillez réessayer.'
    });
  });

  it('should clear userMessage after sending', () => {
    component.userMessage = 'Où se trouve le Bloc Prepa ?';
    component.sendMessage();

    expect(component.userMessage).toBe('');
  });

  it('should not send message if userMessage is empty', () => {
    component.userMessage = '   ';
    component.sendMessage();

    expect(component.messages.length).toBe(1);
    httpMock.expectNone('http://navigation-bot:8001/ask');
  });

  it('should initialize Leaflet map when a message with location is added', fakeAsync(() => {
    spyOn(document, 'getElementById').and.returnValue(document.createElement('div'));

    const mapSpy = spyOn(L, 'map').and.returnValue({
      setView: jasmine.createSpy('setView').and.returnValue({}),
      removeLayer: jasmine.createSpy('removeLayer'),
      addTo: jasmine.createSpy('addTo').and.returnValue({}),
    } as any);

    spyOn(L, 'tileLayer').and.returnValue({ addTo: jasmine.createSpy('addTo').and.returnValue({}) } as any);
    spyOn(L, 'marker').and.returnValue({
      addTo: jasmine.createSpy('addTo').and.returnValue({}),
      bindPopup: jasmine.createSpy('bindPopup').and.returnValue({}),
      openPopup: jasmine.createSpy('openPopup')
    } as any);
    spyOn(L, 'icon').and.returnValue({} as any);

    component.messages.push({
      sender: 'bot',
      text: "L'emplacement 'Bloc Prepa' se trouve ici :",
      location: { lat: 36.8344411, lng: 10.1456052, title: 'Bloc Prepa' },
      mapId: 'map-1'
    });

    component['initMaps']();
    tick();

    expect(mapSpy).toHaveBeenCalledWith(jasmine.any(HTMLElement), {
      zoomControl: true,
      scrollWheelZoom: false
    });
    expect(L.marker).toHaveBeenCalledWith([36.8344411, 10.1456052], jasmine.any(Object));
    expect(L.tileLayer).toHaveBeenCalledWith('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', jasmine.any(Object));
  }));
});
