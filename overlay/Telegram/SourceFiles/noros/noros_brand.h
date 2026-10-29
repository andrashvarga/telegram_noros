/*
Noros fork of Telegram Desktop: brand (icon / name / title logo), themes,
design (Material / Liquid Glass) and anonymous reading.

Licensed under GPLv3 like the rest of Telegram Desktop.
*/
#pragma once

#include <QtGui/QIcon>
#include <QtGui/QImage>
#include <rpl/producer.h>

namespace Noros {

enum class Icon : int { Noros = 0, Valutix = 1, RioPay = 2 };
enum class Theme : int { Light = 0, Dark = 1, Noros = 2, Valutix = 3, RioPay = 4 };
enum class Design : int { Material = 0, Glass = 1 };

// Loads saved choices from tdata/noros.json. Call once at startup.
void Start();

[[nodiscard]] Icon CurrentIcon();
[[nodiscard]] Theme CurrentTheme();
[[nodiscard]] Design CurrentDesign();
[[nodiscard]] bool AnonymousRead();

// Setting the icon renames the application and swaps all logos.
void SetIcon(Icon icon);
// Setting theme / design applies the matching embedded .tdesktop-theme.
void SetTheme(Theme theme);
void SetDesign(Design design);
void SetAnonymousRead(bool enabled);

[[nodiscard]] QString AppName();
[[nodiscard]] QString IconName(Icon icon);
[[nodiscard]] QString ThemeName(Theme theme);
[[nodiscard]] QString DesignName(Design design);

// 256px icon of the currently selected brand.
[[nodiscard]] const QImage &LogoImage();
[[nodiscard]] QIcon AppIcon();
[[nodiscard]] QImage IconPreview(Icon icon, int size);

// Fires when icon / name changes.
[[nodiscard]] rpl::producer<> BrandChanges();

// Puts the brand logo into the top-left corner of the window title bar.
void AttachTitleLogo(not_null<QWidget*> title);

} // namespace Noros
