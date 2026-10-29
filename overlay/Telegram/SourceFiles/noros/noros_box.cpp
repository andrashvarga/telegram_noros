/*
Noros fork of Telegram Desktop. Licensed under GPLv3.
*/
#include "noros/noros_box.h"

#include "noros/noros_brand.h"
#include "ui/layers/generic_box.h"
#include "ui/painter.h"
#include "ui/qt_object_factory.h"
#include "ui/style/style_core_scale.h"
#include "ui/rp_widget.h"
#include "ui/vertical_list.h"
#include "ui/widgets/checkbox.h"
#include "ui/widgets/labels.h"
#include "ui/wrap/vertical_layout.h"
#include "styles/style_boxes.h"
#include "styles/style_layers.h"

namespace Noros {
namespace {

// One selectable brand: big preview of the app icon + radio button with name.
class IconRow final : public Ui::RpWidget {
public:
	IconRow(
		QWidget *parent,
		std::shared_ptr<Ui::RadiobuttonGroup> group,
		Icon icon)
	: RpWidget(parent)
	, _icon(icon)
	, _image(IconPreview(icon, 48 * style::DevicePixelRatio()))
	, _radio(
		this,
		std::move(group),
		int(icon),
		IconName(icon),
		st::defaultBoxCheckbox) {
		_image.setDevicePixelRatio(style::DevicePixelRatio());
		resize(width(), 56);
		sizeValue(
		) | rpl::on_next([=](QSize size) {
			_radio->moveToLeft(64, (size.height() - _radio->height()) / 2);
		}, lifetime());
	}

protected:
	int resizeGetHeight(int newWidth) override {
		return 56;
	}
	void paintEvent(QPaintEvent *e) override {
		auto p = QPainter(this);
		p.setRenderHint(QPainter::SmoothPixmapTransform);
		p.drawImage(QRect(4, 4, 48, 48), _image);
	}

private:
	Icon _icon;
	QImage _image;
	object_ptr<Ui::Radiobutton> _radio;

};

void AddRadioRow(
		not_null<Ui::VerticalLayout*> content,
		std::shared_ptr<Ui::RadiobuttonGroup> group,
		int value,
		const QString &text) {
	content->add(
		object_ptr<Ui::Radiobutton>(
			content,
			std::move(group),
			value,
			text,
			st::defaultBoxCheckbox),
		st::boxRowPadding + QMargins(0, 4, 0, 4));
}

} // namespace

void StyleBox(not_null<Ui::GenericBox*> box) {
	box->setTitle(rpl::single(u"Оформление"_q));
	box->setWidth(st::boxWideWidth);
	const auto content = box->verticalLayout();

	// --- Icon (name + logo in the window's top-left corner)
	Ui::AddSubsectionTitle(
		content,
		rpl::single(u"Иконка и название приложения"_q));
	const auto iconGroup = std::make_shared<Ui::RadiobuttonGroup>(
		int(CurrentIcon()));
	for (const auto icon : { Icon::Noros, Icon::Valutix, Icon::RioPay }) {
		content->add(
			object_ptr<IconRow>(content, iconGroup, icon),
			st::boxRowPadding);
	}
	iconGroup->setChangedCallback([=](int value) {
		SetIcon(Icon(value));
	});
	Ui::AddSkip(content);

	// --- Colour theme (hard restyle of the whole client)
	Ui::AddSubsectionTitle(content, rpl::single(u"Тема"_q));
	const auto themeGroup = std::make_shared<Ui::RadiobuttonGroup>(
		int(CurrentTheme()));
	for (const auto theme : {
		Theme::Light,
		Theme::Dark,
		Theme::Noros,
		Theme::Valutix,
		Theme::RioPay,
	}) {
		AddRadioRow(content, themeGroup, int(theme), ThemeName(theme));
	}
	themeGroup->setChangedCallback([=](int value) {
		SetTheme(Theme(value));
	});
	Ui::AddSkip(content);

	// --- Design language
	Ui::AddSubsectionTitle(content, rpl::single(u"Дизайн"_q));
	const auto designGroup = std::make_shared<Ui::RadiobuttonGroup>(
		int(CurrentDesign()));
	AddRadioRow(
		content,
		designGroup,
		int(Design::Material),
		DesignName(Design::Material));
	AddRadioRow(
		content,
		designGroup,
		int(Design::Glass),
		DesignName(Design::Glass));
	designGroup->setChangedCallback([=](int value) {
		SetDesign(Design(value));
	});
	Ui::AddSkip(content);

	// --- Privacy
	Ui::AddSubsectionTitle(content, rpl::single(u"Приватность"_q));
	const auto anonymous = content->add(
		object_ptr<Ui::Checkbox>(
			content,
			u"Читать анонимно (без отметки «прочитано»)"_q,
			AnonymousRead(),
			st::defaultBoxCheckbox),
		st::boxRowPadding + QMargins(0, 4, 0, 4));
	anonymous->checkedChanges(
	) | rpl::on_next([=](bool checked) {
		SetAnonymousRead(checked);
	}, anonymous->lifetime());
	Ui::AddDividerText(
		content,
		rpl::single(TextWithEntities{
			u"Собеседники не увидят, что вы прочитали сообщение. "
			"В вашем клиенте чат отображается прочитанным."_q }));

	box->addButton(rpl::single(u"Готово"_q), [=] { box->closeBox(); });
}

} // namespace Noros
