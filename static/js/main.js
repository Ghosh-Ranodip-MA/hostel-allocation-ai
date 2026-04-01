/**
 * Hostel Allocation System – Client-side helpers
 * -----------------------------------------------
 */

document.addEventListener('DOMContentLoaded', () => {

  // ── Auto-dismiss alerts after 5 seconds ──
  document.querySelectorAll('.alert-dismissible').forEach(alert => {
    setTimeout(() => {
      const btn = alert.querySelector('.btn-close');
      if (btn) btn.click();
    }, 5000);
  });

  // ── Simple table search / filter ──
  const searchInputs = document.querySelectorAll('[data-table-filter]');
  searchInputs.forEach(input => {
    const tableId = input.getAttribute('data-table-filter');
    const table = document.getElementById(tableId);
    if (!table) return;

    input.addEventListener('input', () => {
      const term = input.value.toLowerCase();
      table.querySelectorAll('tbody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
      });
    });
  });

  // ── Room selection on allocate page ──
  document.querySelectorAll('.room-option').forEach(option => {
    option.addEventListener('click', () => {
      document.querySelectorAll('.room-option').forEach(o => o.classList.remove('selected'));
      option.classList.add('selected');
      const radio = option.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
    });
  });

  // ── Confirmation dialogs for dangerous actions ──
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (e) => {
      if (!confirm(el.getAttribute('data-confirm'))) {
        e.preventDefault();
      }
    });
  });
});