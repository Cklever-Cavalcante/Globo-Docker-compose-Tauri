import { ComponentFixture, TestBed } from '@angular/core/testing';

import { OccurrenceDetails } from './occurrence-details';

describe('OccurrenceDetails', () => {
  let component: OccurrenceDetails;
  let fixture: ComponentFixture<OccurrenceDetails>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OccurrenceDetails]
    })
    .compileComponents();

    fixture = TestBed.createComponent(OccurrenceDetails);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
