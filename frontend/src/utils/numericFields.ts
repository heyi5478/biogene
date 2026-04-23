import { FieldDefinition, ModuleId, MODULE_FIELDS } from '@/types/medical';

export function numericFieldsFor(moduleId: ModuleId): FieldDefinition[] {
  return MODULE_FIELDS[moduleId].filter((f) => f.type === 'number');
}
