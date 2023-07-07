import { CUSTOM_ELEMENTS_SCHEMA, NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MinimalRoutingModule } from './minimal-routing.module';
import { InputNumberModule } from 'primeng/inputnumber';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { RadioButtonModule } from 'primeng/radiobutton';
import { MinimalComponent } from '../minimal.component';
import { TooltipModule } from 'primeng/tooltip';
import { MultiSelectModule } from 'primeng/multiselect';
import { DropdownModule } from 'primeng/dropdown';
import { AccordionModule } from 'primeng/accordion';
@NgModule({
    imports: [
        FormsModule,
        CommonModule,
        MinimalRoutingModule,

        ReactiveFormsModule,

        InputNumberModule,
        RadioButtonModule,
        TooltipModule,
        MultiSelectModule,
        DropdownModule,
        AccordionModule
    ],
    declarations: [MinimalComponent],
    schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class MinimalModule { }