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
            "ThumbnailActions": "ThumbnailActions::ShowSelectionButtonOnly",
            "ThumbnailBarIsVisible": "true",
            "ThumbnailBarOrientation": "Horizontal",
            "ThumbnailBarRowCount": "1",
            "UrlNavigatorIsEditable": "false",
            "UrlNavigatorShowFullPath": "false",
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
            "ThumbnailDetails": "1",
            "ThumbnailAspectRatio": "1.5",
            "ListVideos": "true",
            "AutoplayVideos": "false",
            "Sorting": "Sorting::Name",
            "SortDescending": "false",
        },
        "SideBar": {"IsVisible ViewMode": "false"},
        "FullScreen": {
            "ShowFullScreenThumbnails": "true",
            "FullScreenModeActive": "false",
        },
        "slide show": {"interval": "5", "random": "false", "loop": "false"},
    }
