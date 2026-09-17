# Gwenview 26.08.1 native sidebar and styling contract

Inspected actual `evidence/aven/round-06/photos-first-1x.png` after the first
deployment. The sidebar is visible at the requested 208 pixels, native toolbar
labels are hidden, and the caption-free image grid retains aspect ratios. The
URL navigator has an unreadable dark background, the sidebar is still white,
and its horizontal scrollbar has a dark track. Shared styling must correct these
before a visual pass. The 240 pixel grid produces only three columns at the
captured 1200 pixel window width. A 176 pixel shared `icon.photoGrid` token brings
its native slot spacing closer to the reference's five-column density.

## Exact selectors for the root-owned compatibility stylesheet

| Element | Qt selector | Source |
| --- | --- | --- |
| Breadcrumb container | `QWidget#mUrlNavigatorContainer` | `app/browsemainpage.ui` |
| Breadcrumb control | `KUrlNavigator` | `app/browsemainpage.cpp` |
| Sidebar shell | `Gwenview--SideBar` | `app/sidebar.h`, inherits `QTabWidget` |
| Folders page | `QWidget#folders` | `app/mainwindow.cpp` |
| Folder tree | `QWidget#folders QTreeView` | `app/folderviewcontextmanageritem.cpp` |
| Sidebar tab buttons | `Gwenview--SideBar QTabBar` | `app/sidebar.cpp` |
| Thumbnail grid | `Gwenview--ThumbnailView#mThumbnailView` | `app/browsemainpage.ui` |
| Browse footer | `QWidget#mStatusBarContainer` | `app/browsemainpage.ui` |

`UrlDropTreeView` has no `Q_OBJECT`, so its runtime Qt class selector is
`QTreeView`; selecting `UrlDropTreeView` will not work. Qt stylesheet type names
replace the C++ namespace separator `::` with `--`.

Use the folders ancestor to scope sidebar tree/scrollbar colors. Preserve the
native tree's selection, branches, scrolling, context actions and drop handling.
The footer and thumbnail viewport should remain distinct from the gray sidebar.
Do not apply a blanket background to every widget or image viewport.

## Why no simpler Places preference was added

Gwenview already uses its `PlaceTreeModel` backed by `KFilePlacesModel` here.
`USE_PLACETREE` is a compile-time definition in
`app/folderviewcontextmanageritem.h`, not a user configuration option.
`PlaceTreeModel` directly forwards every root row and never filters
`KFilePlacesModel::isHidden`. It has no KConfig options for a flat list, a
photo-only root, or excluding hidden Places. This explains why Desktop, Music,
Recent Locations and system volumes reappear here despite Dolphin correctly
honoring their native hidden state.

The supported `SideBarPage` choices are `folders`, `information` and
`operations`. Folders remains the only navigation page. Replacing it with
Photos-like semantic collections or respecting hidden rows requires an upstream
application change; inventing preference keys would silently do nothing.

No settings, image associations or preview handoffs were changed during this
follow-up inspection. Root owns the native launcher stylesheet integration.

Sources: [Gwenview folder view](https://github.com/KDE/gwenview/blob/v26.08.1/app/folderviewcontextmanageritem.cpp),
[PlaceTreeModel](https://github.com/KDE/gwenview/blob/v26.08.1/lib/placetreemodel.cpp),
[Browse UI](https://github.com/KDE/gwenview/blob/v26.08.1/app/browsemainpage.ui),
[sidebar](https://github.com/KDE/gwenview/blob/v26.08.1/app/sidebar.h),
[Qt namespace selectors](https://doc.qt.io/qt-6/stylesheet-syntax.html).
