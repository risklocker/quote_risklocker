"use client";

import { Info } from "lucide-react";

type DraftField = {
  value?: string | null;
  status?: string;
  message?: string;
  warnings?: string[];
};

type ReviewGroup = {
  id: string;
  title: string;
  collapsed?: boolean;
  fields: string[];
};

type ReviewSchema = {
  groups?: ReviewGroup[];
};

const labels: Record<string, string> = {
  insurance_type: "Insurance Type",
  insurance_company: "Insurance Company",
  source_template_category: "Template Category",
  selected_package: "Selected Package",
  product_name: "Source Product",
  customer_name: "Customer Name",
  issue_date: "Issued Date",
  valid_until: "Valid Until",
  vehicle_no: "Vehicle No",
  vehicle_class: "Vehicle Class",
  car_brand: "Car Brand",
  car_model: "Car Model",
  vehicle_year: "Vehicle Year",
  engine_cc: "Capacity",
  engine_no: "Engine/Motor No",
  chassis_no: "Chassis No",
  cover_period: "Cover Period",
  coverage_type: "Coverage Type",
  coverage_amount: "Coverage Amount",
  market_value: "Market Value",
  agreed_value: "Agreed Value",
  excess_amount: "Excess Amount",
  basic_premium_vehicle: "Basic Premium (Vehicle)",
  basic_premium_trailer: "Basic Premium (Trailer)",
  premium: "Insurance Premium",
  ncd_amount: "NCD Amount",
  loading_amount: "Loading",
  all_riders_amount: "All Riders",
  optional_cover_amount: "Optional Cover Amount",
  service_tax: "Service Tax",
  stamp_duty: "Stamp Duty",
  gross_premium: "Gross Premium",
  roadtax: "Roadtax",
  service_fee: "Runner Fee",
  total_amount: "Total Premium",
  ncd_percent: "NCD",
  optional_covers: "Optional Covers",
  benefits_selected: "Specials",
  add_ons_selected: "Add-ons",
  notes: "Notes"
};

const fallbackGroups: ReviewGroup[] = [
  {
    id: "quotation_values",
    title: "Quotation Values",
    fields: ["coverage_type", "cover_period", "car_model", "ncd_percent", "coverage_amount", "premium", "roadtax", "service_fee", "total_amount"]
  },
  {
    id: "source_details",
    title: "More Source Details",
    collapsed: true,
    fields: ["insurance_company", "source_template_category", "product_name", "customer_name", "vehicle_no", "vehicle_year", "engine_cc", "engine_no", "chassis_no", "market_value", "service_tax", "stamp_duty", "gross_premium", "optional_covers", "notes"]
  }
];

const longFields = new Set(["benefits_selected", "add_ons_selected", "optional_covers", "notes"]);

function FieldEditor({
  fieldName,
  field,
  hint,
  onChange
}: {
  fieldName: string;
  field: DraftField;
  hint?: string;
  onChange: (field: string, value: string) => void;
}) {
  const label = labels[fieldName] || fieldName;
  const needsCheck = field.status === "check_needed";
  return (
    <div className={`grid gap-2 rounded-md border p-3 sm:grid-cols-[180px_minmax(0,1fr)] ${needsCheck ? "border-amber-300 bg-amber-50" : "border-rl-line bg-white"}`}>
      <label className="font-bold text-rl-textStrong" htmlFor={`field-${fieldName}`}>
        {label}
      </label>
      <div className="grid gap-1">
        {longFields.has(fieldName) ? (
          <textarea
            id={`field-${fieldName}`}
            className="rl-input min-h-24 resize-y"
            aria-invalid={needsCheck}
            value={field.value || ""}
            onChange={(event) => onChange(fieldName, event.target.value)}
          />
        ) : (
          <input
            id={`field-${fieldName}`}
            className="rl-input"
            aria-invalid={needsCheck}
            value={field.value || ""}
            onChange={(event) => onChange(fieldName, event.target.value)}
          />
        )}
        <div className="flex flex-wrap items-center gap-2">
          {needsCheck ? <p className="text-sm font-bold text-rl-warning">Please check this value.</p> : null}
          {hint ? (
            <span className="inline-flex items-center gap-1 text-xs font-bold text-rl-text" title={hint} aria-label={hint}>
              <Info aria-hidden="true" size={14} />
              Source
            </span>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function DraftFieldTable({
  fields,
  reviewSchema,
  fieldHints,
  onChange
}: {
  fields: Record<string, DraftField>;
  reviewSchema?: ReviewSchema;
  fieldHints?: Record<string, string>;
  onChange: (field: string, value: string) => void;
}) {
  const groups = reviewSchema?.groups?.length ? reviewSchema.groups : fallbackGroups;
  return (
    <div className="grid gap-4">
      {groups.map((group) => {
        const content = (
          <div className="mt-3 grid gap-3">
            {group.fields.map((fieldName) => (
              <FieldEditor key={fieldName} fieldName={fieldName} field={fields[fieldName] || {}} hint={fieldHints?.[fieldName]} onChange={onChange} />
            ))}
          </div>
        );
        if (group.collapsed) {
          return (
            <details key={group.id} className="rl-panel p-4">
              <summary className="cursor-pointer font-bold text-rl-textStrong">{group.title}</summary>
              {content}
            </details>
          );
        }
        return (
          <section key={group.id} className="rl-panel p-4">
            <h2 className="text-lg font-bold text-rl-textStrong">{group.title}</h2>
            {content}
          </section>
        );
      })}
    </div>
  );
}
