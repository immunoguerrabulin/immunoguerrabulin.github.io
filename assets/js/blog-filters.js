document.addEventListener("DOMContentLoaded", () => {
  const filtersRoot = document.querySelector("[data-blog-filters]");
  const postList = document.querySelector(".post-list");

  if (!filtersRoot || !postList) {
    return;
  }

  const buttons = Array.from(filtersRoot.querySelectorAll("[data-filter]"));
  const posts = Array.from(postList.querySelectorAll("[data-post-categories]"));
  const emptyState = postList.querySelector("[data-filter-empty]");
  const status = filtersRoot.querySelector("[data-filter-status]");

  if (!buttons.length || !posts.length) {
    return;
  }

  const totalPosts = posts.length;
  const buttonByFilter = new Map(buttons.map((button) => [button.dataset.filter, button]));

  const updateUrl = (filter) => {
    const url = new URL(window.location.href);

    if (filter === "all") {
      url.searchParams.delete("category");
    } else {
      url.searchParams.set("category", filter);
    }

    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  };

  const applyFilter = (filter, shouldUpdateUrl) => {
    const activeFilter = buttonByFilter.has(filter) ? filter : "all";
    let visiblePosts = 0;

    posts.forEach((post) => {
      const categories = (post.dataset.postCategories || "")
        .split("|")
        .map((value) => value.trim())
        .filter(Boolean);
      const isVisible = activeFilter === "all" || categories.includes(activeFilter);

      post.hidden = !isVisible;
      if (isVisible) {
        visiblePosts += 1;
      }
    });

    buttons.forEach((button) => {
      const isActive = button.dataset.filter === activeFilter;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });

    if (status) {
      const label = (buttonByFilter.get(activeFilter)?.textContent || "All").trim();
      status.textContent =
        activeFilter === "all"
          ? `Showing all ${totalPosts} posts`
          : `Showing ${visiblePosts} of ${totalPosts} posts in ${label}`;
    }

    if (emptyState) {
      emptyState.hidden = visiblePosts !== 0;
    }

    if (shouldUpdateUrl) {
      updateUrl(activeFilter);
    }
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      applyFilter(button.dataset.filter, true);
    });
  });

  const initialFilter = new URLSearchParams(window.location.search).get("category");
  applyFilter((initialFilter || "all").toLowerCase(), false);
});
