/*
Noros fork of Telegram Desktop.
Licensed under GPLv3 like the rest of Telegram Desktop.
*/
#include "noros/noros_brand.h"

#include "settings.h"
#include "window/themes/window_theme.h"
#include "ui/rp_widget.h"
#include "ui/painter.h"
#include "ui/qt_object_factory.h"
#include "ui/style/style_core_scale.h"
#include "styles/palette.h"

#include <QtCore/QDir>
#include <QtCore/QFile>
#include <QtCore/QJsonDocument>
#include <QtCore/QJsonObject>
#include <QtGui/QGuiApplication>
#include <QtWidgets/QApplication>
#include <rpl/event_stream.h>

namespace Noros {
namespace {

struct State {
	Icon icon = Icon::Noros;
	Theme theme = Theme::Noros;
	Design design = Design::Material;
	bool anonymousRead = false;
	bool loaded = false;
};

State &Data() {
	static auto result = State();
	return result;
}

rpl::event_stream<> &Changes() {
	static auto result = rpl::event_stream<>();
	return result;
}

QString StatePath() {
	return cWorkingDir() + u"tdata/noros.json"_q;
}

void Save() {
	const auto &d = Data();
	auto object = QJsonObject();
	object.insert(u"icon"_q, int(d.icon));
	object.insert(u"theme"_q, int(d.theme));
	object.insert(u"design"_q, int(d.design));
	object.insert(u"anonymousRead"_q, d.anonymousRead);
	QDir().mkpath(cWorkingDir() + u"tdata"_q);
	auto file = QFile(StatePath());
	if (file.open(QIODevice::WriteOnly | QIODevice::Truncate)) {
		file.write(QJsonDocument(object).toJson(QJsonDocument::Compact));
	}
}

template <typename Enum>
Enum Pick(const QJsonObject &o, const QString &key, Enum fallback, int max) {
	const auto v = o.value(key).toInt(int(fallback));
	return (v >= 0 && v <= max) ? Enum(v) : fallback;
}

QString IconKey(Icon icon) {
	switch (icon) {
	case Icon::Valutix: return u"valutix"_q;
	case Icon::RioPay: return u"riopay"_q;
	default: return u"noros"_q;
	}
}

QString ThemeKey(Theme theme) {
	switch (theme) {
	case Theme::Light: return u"light"_q;
	case Theme::Dark: return u"dark"_q;
	case Theme::Valutix: return u"valutix"_q;
	case Theme::RioPay: return u"riopay"_q;
	default: return u"noros"_q;
	}
}

QImage &LogoStorage() {
	static auto result = QImage();
	return result;
}

void RefreshLogo() {
	LogoStorage() = IconPreview(Data().icon, 256);
}

void ApplyCurrentTheme() {
	const auto &d = Data();
	const auto path = u":/noros/themes/%1_%2.tdesktop-theme"_q.arg(
		ThemeKey(d.theme),
		d.design == Design::Glass ? u"glass"_q : u"material"_q);
	Window::Theme::ApplyDefaultWithPath(path);
	Window::Theme::KeepApplied();
}

class TitleLogo final : public Ui::RpWidget {
public:
	explicit TitleLogo(QWidget *parent) : RpWidget(parent) {
		setObjectName(u"noros_title_logo"_q);
		setAttribute(Qt::WA_TransparentForMouseEvents);
		BrandChanges() | rpl::on_next([=] {
			refresh();
		}, lifetime());
		refresh();
		if (const auto p = parentWidget()) {
			p->installEventFilter(this);
		}
	}

protected:
	bool eventFilter(QObject *o, QEvent *e) override {
		if (o == parentWidget() && e->type() == QEvent::Resize) {
			place();
		}
		return RpWidget::eventFilter(o, e);
	}

	void paintEvent(QPaintEvent *e) override {
		auto p = QPainter(this);
		p.setRenderHint(QPainter::SmoothPixmapTransform);
		const auto light = st::titleBgActive->c.lightness() > 140;
		const auto image = TitleImage(light);
		if (image.isNull()) {
			return;
		}
		p.drawImage(QRect(0, 0, width(), height()), image);
	}

private:
	[[nodiscard]] QImage TitleImage(bool lightTitle) const {
		return QImage(u":/noros/logo_%1_%2.png"_q.arg(
			IconKey(Data().icon),
			lightTitle ? u"onlight"_q : u"ondark"_q));
	}
	void refresh() {
		const auto image = TitleImage(true);
		const auto h = 14;
		const auto w = image.isNull()
			? 0
			: std::max(1, int(std::round(image.width() * double(h) / image.height())));
		resize(w, h);
		place();
		update();
	}
	void place() {
		if (const auto p = parentWidget()) {
			move(10, std::max(0, (p->height() - height()) / 2));
		}
		show();
		raise();
	}

};

} // namespace

void Start() {
	auto &d = Data();
	if (d.loaded) {
		return;
	}
	d.loaded = true;
	auto file = QFile(StatePath());
	if (file.open(QIODevice::ReadOnly)) {
		const auto doc = QJsonDocument::fromJson(file.readAll());
		const auto o = doc.object();
		d.icon = Pick(o, u"icon"_q, Icon::Noros, 2);
		d.theme = Pick(o, u"theme"_q, Theme::Noros, 4);
		d.design = Pick(o, u"design"_q, Design::Material, 1);
		d.anonymousRead = o.value(u"anonymousRead"_q).toBool(false);
	}
	RefreshLogo();
}

Icon CurrentIcon() { Start(); return Data().icon; }
Theme CurrentTheme() { Start(); return Data().theme; }
Design CurrentDesign() { Start(); return Data().design; }
bool AnonymousRead() { return Data().anonymousRead; }

void SetIcon(Icon icon) {
	Start();
	Data().icon = icon;
	Save();
	RefreshLogo();
	QApplication::setWindowIcon(AppIcon());
	QGuiApplication::setApplicationDisplayName(AppName());
	Changes().fire({});
}

void SetTheme(Theme theme) {
	Start();
	Data().theme = theme;
	Save();
	ApplyCurrentTheme();
}

void SetDesign(Design design) {
	Start();
	Data().design = design;
	Save();
	ApplyCurrentTheme();
}

void SetAnonymousRead(bool enabled) {
	Start();
	Data().anonymousRead = enabled;
	Save();
}

QString IconName(Icon icon) {
	switch (icon) {
	case Icon::Valutix: return u"Valutix"_q;
	case Icon::RioPay: return u"RioPay"_q;
	default: return u"Noros"_q;
	}
}

QString AppName() {
	Start();
	return IconName(Data().icon);
}

QString ThemeName(Theme theme) {
	switch (theme) {
	case Theme::Light: return u"Светлая"_q;
	case Theme::Dark: return u"Тёмная"_q;
	case Theme::Valutix: return u"Valutix"_q;
	case Theme::RioPay: return u"RioPay"_q;
	default: return u"Noros"_q;
	}
}

QString DesignName(Design design) {
	return (design == Design::Glass)
		? u"Liquid Glass"_q
		: u"Material"_q;
}

const QImage &LogoImage() {
	Start();
	return LogoStorage();
}

QImage IconPreview(Icon icon, int size) {
	const auto sizes = { 16, 32, 48, 64, 128, 256, 512 };
	auto best = 512;
	for (const auto s : sizes) {
		if (s >= size) {
			best = s;
			break;
		}
	}
	auto image = QImage(u":/noros/icon_%1_%2.png"_q.arg(IconKey(icon)).arg(best));
	if (image.isNull()) {
		return image;
	}
	return (image.width() == size)
		? image
		: image.scaled(size, size, Qt::KeepAspectRatio, Qt::SmoothTransformation);
}

QIcon AppIcon() {
	auto result = QIcon();
	for (const auto s : { 16, 32, 48, 64, 128, 256 }) {
		result.addPixmap(QPixmap::fromImage(IconPreview(Data().icon, s)));
	}
	return result;
}

rpl::producer<> BrandChanges() {
	return Changes().events();
}

void AttachTitleLogo(not_null<QWidget*> title) {
	if (title->findChild<QWidget*>(u"noros_title_logo"_q, Qt::FindDirectChildrenOnly)) {
		return;
	}
	Ui::CreateChild<TitleLogo>(title.get());
}

} // namespace Noros
