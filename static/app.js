// Frontend logic: talks to the Flask REST API with fetch().
const FIELDS = ["full_name", "dob", "email", "glucose", "haemoglobin", "cholesterol"];
let patients = [];

// Assignment test data, used only to pre-fill the form (entries are still submitted through the app).
const TEST_DATA = [
  ["Robyn Pears", "28.01.1960", "robyn@gmail.com", 232, 13.5, 180],
  ["John Hunter", "10.12.1990", "hunter@gmail", 94, 15, 200],
  ["Darryl Tim", "12.11.1993", "timd@smh.com.au", 240, 18.6, 326],
  ["Peter Larry", "31.11.2001", "Larry@hotmail.com", 88, 11.5, 165],
  ["Sam Kerr", "09.12.2006", "sam@news.com.au", 198, 8.9, 192],
  ["Robyn Pears", "28.01.1960", "robyn@gmail.com", 232, 13.5, 180],
  ["Madison XI", "12.09.1998", "madison@hotmail.com", 85, 7.6, 163],
  ["Kris Wu", "19.10.2030", "Kris.wu.gmail.com", 79, 16.5, 197],
  ["Tenille Singh", "30.11.1991", "Tenille@yahoo.com", 101, 15, 310],
  ["Prem Kumar", "28.04.1990", "prem@telstra.com", 155, 12.5, 265],
];

const el = (id) => document.getElementById(id);
const form = el("patient-form");
const rowsEl = el("rows");
const saveBtn = el("save-btn");
const cancelBtn = el("cancel-btn");
const formAlert = el("form-alert");

function showToast(message, isError) {
  const toast = el("toast");
  toast.className = "toast align-items-center border-0 text-bg-" + (isError ? "danger" : "success");
  el("toast-body").textContent = message;
  bootstrap.Toast.getOrCreateInstance(toast, { delay: 3500 }).show();
}

function clearErrors() {
  FIELDS.forEach((f) => el(f).classList.remove("is-invalid"));
  formAlert.classList.add("d-none");
}

function showErrors(errors) {
  clearErrors();
  const unplaced = [];
  Object.entries(errors).forEach(([field, message]) => {
    const input = FIELDS.includes(field) ? el(field) : null;
    if (input) {
      input.classList.add("is-invalid");
      input.parentElement.querySelector(".invalid-feedback").textContent = message;
    } else {
      unplaced.push(message);
    }
  });
  if (unplaced.length) {
    formAlert.className = "alert alert-danger";
    formAlert.textContent = unplaced.join(" ");
  }
  const first = FIELDS.find((f) => errors[f]);
  if (first) el(first).focus();
}

function resetForm() {
  form.reset();
  el("patient-id").value = "";
  el("form-title").textContent = "Add patient";
  saveBtn.textContent = "Save patient";
  cancelBtn.classList.add("d-none");
  el("quickfill").value = "";
  clearErrors();
  renderRows();
}

async function loadPatients() {
  const res = await fetch("/api/patients");
  patients = await res.json();
  renderRows();
}

function renderRows() {
  const editingId = el("patient-id").value;
  rowsEl.innerHTML = "";
  patients.forEach((p) => {
    const tr = document.createElement("tr");
    if (String(p.id) === editingId) tr.className = "editing";
    [p.id, p.full_name, p.dob, p.email, p.glucose, p.haemoglobin, p.cholesterol].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value;
      tr.appendChild(td);
    });
    const remarks = document.createElement("td");
    remarks.className = "remarks";
    remarks.textContent = p.remarks || "";
    tr.appendChild(remarks);

    const actions = document.createElement("td");
    actions.className = "actions";
    const edit = document.createElement("button");
    edit.className = "btn btn-sm btn-outline-secondary me-1";
    edit.textContent = "Edit";
    edit.addEventListener("click", () => startEdit(p));
    const del = document.createElement("button");
    del.className = "btn btn-sm btn-outline-danger";
    del.textContent = "Delete";
    del.addEventListener("click", () => removePatient(p));
    actions.append(edit, del);
    tr.appendChild(actions);
    rowsEl.appendChild(tr);
  });
  el("count").textContent = patients.length + (patients.length === 1 ? " record" : " records");
  el("empty").classList.toggle("d-none", patients.length > 0);
}

function startEdit(p) {
  clearErrors();
  el("patient-id").value = p.id;
  FIELDS.forEach((f) => (el(f).value = p[f]));
  el("form-title").textContent = "Edit patient #" + p.id;
  saveBtn.textContent = "Update patient";
  cancelBtn.classList.remove("d-none");
  renderRows();
  el("email").focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function removePatient(p) {
  if (!confirm("Delete the record for " + p.full_name + "?")) return;
  const res = await fetch("/api/patients/" + p.id, { method: "DELETE" });
  if (res.ok) {
    showToast("Deleted " + p.full_name + ".");
    if (el("patient-id").value === String(p.id)) resetForm();
    await loadPatients();
  } else {
    showToast("Could not delete the record.", true);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearErrors();
  const payload = {};
  FIELDS.forEach((f) => (payload[f] = el(f).value));
  const id = el("patient-id").value;
  const idleLabel = id ? "Update patient" : "Save patient";

  saveBtn.disabled = true;
  saveBtn.textContent = "Checking and saving...";
  try {
    const res = await fetch(id ? "/api/patients/" + id : "/api/patients", {
      method: id ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await res.json();
    if (!res.ok) {
      showErrors(body.errors || { general: "Something went wrong." });
      showToast("Not saved. Fix the highlighted fields.", true);
    } else {
      showToast(id ? "Patient updated." : "Patient saved.");
      resetForm();
      await loadPatients();
    }
  } catch (err) {
    showToast("Could not reach the server.", true);
  } finally {
    saveBtn.disabled = false;
    if (saveBtn.textContent.startsWith("Checking")) saveBtn.textContent = idleLabel;
  }
});

cancelBtn.addEventListener("click", resetForm);

const quick = el("quickfill");
quick.add(new Option("Choose a test number...", ""));
TEST_DATA.forEach((row, i) => quick.add(new Option("Test " + (i + 1) + ": " + row[0], i)));
quick.addEventListener("change", () => {
  if (quick.value === "") return;
  clearErrors();
  el("patient-id").value = "";
  const row = TEST_DATA[Number(quick.value)];
  FIELDS.forEach((f, i) => (el(f).value = row[i]));
});

loadPatients();
