import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { LostAndFoundComponent } from './lost-and-found.component';

describe('LostAndFoundComponent', () => {
  let component: LostAndFoundComponent;
  let fixture: ComponentFixture<LostAndFoundComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    // Simuler process.env pour les tests
    (process.env as any) = {
      NG_APP_API_URL: 'http://lost-and-found:8002'
    };

    await TestBed.configureTestingModule({
      declarations: [LostAndFoundComponent],
      imports: [
        HttpClientTestingModule,
        FormsModule
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(LostAndFoundComponent);
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

  it('should fetch items on initialization', fakeAsync(() => {
    const mockItems = [
      {
        id: '1',
        type: 'lost',
        description: 'Lost a black wallet',
        location: 'Bloc Prepa',
        contactInfo: 'john.doe@example.com',
        image_path: '/data/test.jpg',
        detections: [{ name: 'wallet', confidence: 0.9 }],
        timestamp: '2023-10-01T10:00:00Z',
        matches: []
      }
    ];

    // ngOnInit appelle fetchItems
    const req = httpMock.expectOne('http://lost-and-found:8002/items');
    expect(req.request.method).toBe('GET');
    req.flush(mockItems);

    tick();

    expect(component.items.length).toBe(1);
    expect(component.filteredItems.length).toBe(1);
    expect(component.items[0].description).toBe('Lost a black wallet');
    expect(component.items[0].image_path).toBe('http://localhost:8002/data/test.jpg');
    expect(component.items[0].expanded).toBeFalse();
  }));

  it('should apply filter correctly', () => {
    component.items = [
      { id: '1', type: 'lost', description: 'Lost a wallet' },
      { id: '2', type: 'found', description: 'Found a wallet' }
    ];

    component.filter = 'lost';
    component.applyFilter();
    expect(component.filteredItems.length).toBe(1);
    expect(component.filteredItems[0].type).toBe('lost');

    component.filter = 'found';
    component.applyFilter();
    expect(component.filteredItems.length).toBe(1);
    expect(component.filteredItems[0].type).toBe('found');

    component.filter = 'all';
    component.applyFilter();
    expect(component.filteredItems.length).toBe(2);
  });

  it('should change filter and apply it', () => {
    component.items = [
      { id: '1', type: 'lost', description: 'Lost a wallet' },
      { id: '2', type: 'found', description: 'Found a wallet' }
    ];

    const spy = spyOn(component, 'applyFilter').and.callThrough();
    component.changeFilter('lost');
    expect(component.filter).toBe('lost');
    expect(spy).toHaveBeenCalled();
    expect(component.filteredItems.length).toBe(1);
    expect(component.filteredItems[0].type).toBe('lost');
  });

  it('should submit item successfully', fakeAsync(() => {
    component.type = 'lost';
    component.description = 'Lost a black wallet';
    component.location = 'Bloc Prepa';
    component.contactInfo = 'john.doe@example.com';
    component.selectedFile = new File(['fake content'], 'test.jpg', { type: 'image/jpeg' });

    const spy = spyOn(component, 'fetchItems').and.callThrough();
    component.submitItem();

    const req = httpMock.expectOne('http://lost-and-found:8002/upload');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.get('type')).toBe('lost');
    expect(req.request.body.get('description')).toBe('Lost a black wallet');
    expect(req.request.body.get('location')).toBe('Bloc Prepa');
    expect(req.request.body.get('contactInfo')).toBe('john.doe@example.com');
    expect(req.request.body.get('file')).toBeTruthy();

    req.flush({ id: '1', detections: [{ name: 'wallet', confidence: 0.9 }] });

    tick();

    expect(spy).toHaveBeenCalled();
    expect(component.description).toBe('');
    expect(component.location).toBe('');
    expect(component.contactInfo).toBe('');
    expect(component.selectedFile).toBeNull();
  }));

  it('should handle error when submitting item', fakeAsync(() => {
    component.type = 'lost';
    component.description = 'Lost a black wallet';
    component.selectedFile = new File(['fake content'], 'test.jpg', { type: 'image/jpeg' });

    const consoleSpy = spyOn(console, 'error');
    component.submitItem();

    const req = httpMock.expectOne('http://lost-and-found:8002/upload');
    req.flush('Error', { status: 500, statusText: 'Server Error' });

    tick();

    expect(consoleSpy).toHaveBeenCalledWith('Error submitting item:', jasmine.anything());
    // Les champs ne doivent pas être réinitialisés en cas d'erreur
    expect(component.description).toBe('Lost a black wallet');
  }));

  it('should set selected file on file input change', () => {
    const mockFile = new File(['fake content'], 'test.jpg', { type: 'image/jpeg' });
    const mockEvent = {
      target: {
        files: [mockFile]
      }
    } as unknown as Event;

    component.onFileSelected(mockEvent);
    expect(component.selectedFile).toBe(mockFile);
  });
});
