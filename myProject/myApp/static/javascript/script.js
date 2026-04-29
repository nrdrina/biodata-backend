document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.querySelector('.toggle-btn');

    // ✅ Reapply sidebar state on page load
    if (localStorage.getItem('sidebarExpanded') === 'true') {
      sidebar.classList.add('expand');
    }

    // ✅ Toggle and save state
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('expand');
      const isExpanded = sidebar.classList.contains('expand');
      localStorage.setItem('sidebarExpanded', isExpanded);
    });
});
