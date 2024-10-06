import { z } from "zod";
import { AttributeSchema, BrochureSchema, PropertySchema } from "../../prisma/generated/zod";

export type BrochureSchema = z.infer<typeof BrochureSchema>;
export const brochureSchema = BrochureSchema;

export type AttributeSchema = z.infer<typeof AttributeSchema>;
export const attributeSchema = AttributeSchema;

export type AttributesObjectSchema = z.infer<typeof attributesObjectSchema>;
export const attributesObjectSchema = z.record(z.string(), z.string());

export type PropertySchema = z.infer<typeof propertySchema>;
export const propertySchema = PropertySchema.omit({
  attributes: true,
}).extend({
  attributes: attributesObjectSchema,
  brochures: z.array(brochureSchema),
});

export type PropertyWithBrochures = z.infer<typeof propertyWithBrochuresSchema>;
export const propertyWithBrochuresSchema = PropertySchema.omit({
  attributes: true,
}).extend({
  brochures: z.array(brochureSchema),
});

export const photoUploadSchema = z.object({
  propertyId: z.string(),
  photoUrl: z.string(),
});

export type CreatePropertySchema = z.infer<typeof createPropertySchema>;
export const createPropertySchema = propertySchema.omit({
  id: true,
  ownerId: true,
}).extend({
  brochures: z.array(brochureSchema.omit({ id: true, propertyId: true })),
});

export type ImportPropertiesInput = z.infer<typeof importPropertiesInput>;
export const importPropertiesInput = z.object({
  properties: z.array(createPropertySchema),
  surveyId: z.string(),
});

export type ImportPropertiesArray = z.infer<typeof importPropertiesArray>;
export const importPropertiesArray = z.array(createPropertySchema);

export type HeaderMappingSchema = z.infer<typeof headerMappingSchema>;
export const headerMappingSchema = z.record(
  z.string(),
  z.object({
    target: z.string(),
    isCustom: z.boolean(),
  }),
);

export type HeaderMapping = z.infer<typeof headerMappingSchema>;