import { Injectable } from "@angular/core";
import { FormGroup } from "@angular/forms";
import { BehaviorSubject } from "rxjs/internal/BehaviorSubject";

@Injectable({
    providedIn: 'root'
})
export class DiagramStorageService {
    private minimalformData = new BehaviorSubject<any>(null);
    currentMinimalFormData = this.minimalformData.asObservable();

    updateMinimalFormData(formGroup: any) {
        this.minimalformData.next(formGroup);
    }

    private advancedformData = new BehaviorSubject<FormGroup>(null);
    currentAdvancedFormData = this.advancedformData.asObservable();

    updateAdvancedFormData(formGroup: FormGroup) {
        this.advancedformData.next(formGroup);
    }

    advancedDataBackup

    advancedDiagramModel: any
    setAdvancedDiagramModel(data) {
        this.advancedDiagramModel = data
    }
    getAdvancedDiagramModel() {
        return this.advancedDiagramModel
    }

    minimalValues: any
    getMinimalValues() {
        return this.minimalValues
    }
    setMinimalValues(minimalValues) {
        this.minimalValues = minimalValues
    }

    advancedAppSettingsFormData: { app_id, nodesSelection, appSettingForm: FormGroup, e2e: any, activeIndex: number, detectorProps, lightSourceProps }

    getAppSettingsFormDataAdvanced() {
        return this.advancedAppSettingsFormData
    }
    setAppSettingsFormDataAdvanced(formData: any) {
        this.advancedAppSettingsFormData = formData;
        this.updateAdvancedFormData(formData.appSettingsForm)
    }

}
