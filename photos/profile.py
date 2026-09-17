"""Public Gwenview KConfig preferences used by the focused Aven prototype."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def preferences(reduced_motion=False):
    tokens = json.loads((ROOT / "visual/tokens.json").read_text())
    return {
        "General": {
            # Auto follows the native Aven color scheme. Never tint image pixels.
            "BackgroundColorMode": "DocumentView::Auto",
            "ThumbnailActions": "ThumbnailActions::None",
            "ThumbnailBarIsVisible": "true",
            "ThumbnailBarOrientation": "Horizontal",
            "ThumbnailBarRowCount": "1",
            "UrlNavigatorIsEditable": "false",
            "UrlNavigatorShowFullPath": "false",
            "SideBarPage": "folders",
            "FullScreenBackground": "FullScreenBackground::Black",
        },
        "ImageView": {
            # Native mutable QSplitter state: leave most space to the photo.
            "ThumbnailSplitterSizes": "680,88",
            "AlphaBackgroundMode": "AbstractImageView::AlphaBackgroundCheckBoard",
            "ApplyExifOrientation": "true",
            "EnableColorManagement": "true",
            "RenderingIntent": "RenderingIntent::Perceptual",
            "AnimationMethod": "DocumentView::NoAnimation" if reduced_motion else "DocumentView::SoftwareAnimation",
            "EnlargeSmallerImages": "false",
            "ZoomMode": "ZoomMode::Autofit",
            "MouseWheelBehavior": "MouseWheelBehavior::Scroll",
            "NavigationEndNotification": "NavigationEndNotification::WarnOnSlideshow",
        },
        "ThumbnailView": {
            "ThumbnailSize": str(tokens["icon"]["photoGrid"]),
            # A photo library grid uses image-only square slots. The native
            # delegate preserves each image's ratio; this does not crop photos.
            "ThumbnailDetails": "0",
            "ThumbnailAspectRatio": "1.0",
            "ListVideos": "true",
            "AutoplayVideos": "false",
            "Sorting": "Sorting::Name",
            "SortDescending": "false",
        },
        "SideBar": {
            # Gwenview deliberately shares this preference between browse and
            # windowed image modes. The F4 action remains available to hide it.
            "IsVisible ViewMode": "true",
            "SideBarSplitterSizes": "208,1024",
        },
        "MainWindow][Toolbar mainToolBar": {
            "IconSize": "18",
            "ToolButtonStyle": "IconOnly",
        },
        "FullScreen": {
            "ShowFullScreenThumbnails": "true",
            "FullScreenModeActive": "false",
        },
        "slide show": {"interval": "5", "random": "false", "loop": "false"},
    }
