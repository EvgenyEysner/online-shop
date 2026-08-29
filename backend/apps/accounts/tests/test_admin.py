from django.contrib import admin
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.accounts.admin import CustomUserAdmin
from apps.accounts.forms import CustomUserChangeForm, CustomUserCreationForm
from apps.accounts.models import CustomUser

PASSWORD = "SecurePass123!"


def make_user(**overrides):
    defaults = dict(
        email="user@example.com",
        first_name="Max",
        last_name="Mustermann",
        password=PASSWORD,
        street="Musterstr.",
        street_no="1",
        zip_code="12345",
        city="Musterstadt",
    )
    defaults.update(overrides)
    return CustomUser.objects.create_user(**defaults)


class CustomUserAdminRegistrationTests(TestCase):

    def test_custom_user_admin_uses_dedicated_forms(self):
        user_admin = admin.site._registry[CustomUser]
        self.assertIsInstance(user_admin, CustomUserAdmin)
        self.assertIs(user_admin.form, CustomUserChangeForm)
        self.assertIs(user_admin.add_form, CustomUserCreationForm)


class CustomUserChangeFormPasswordHashTests(TestCase):
    """
    Der Passwort-Hash darf nicht im Klartext
    im gerenderten Formular-HTML erscheinen.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = make_user(email="pwtest@example.com")

    def test_password_field_does_not_render_raw_hash(self):
        form = CustomUserChangeForm(instance=self.user)
        rendered = str(form["password"])

        self.assertNotIn(self.user.password, rendered)
        # ReadOnlyPasswordHashWidget rendert keinen <input>, sondern nur
        # eine Zusammenfassung (Algorithmus, Hinweistext).
        self.assertNotIn("<input", rendered)

    def test_password_field_is_disabled_and_ignores_submitted_plaintext(self):
        # Selbst wenn jemand versucht, im POST ein Klartext-Passwort als
        # "password" mitzuschicken, muss clean_password() den ursprünglichen
        # (gehashten) Wert zurückgeben - das Feld ist read-only/disabled.
        form = CustomUserChangeForm(
            data={
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "street": self.user.street,
                "street_no": self.user.street_no,
                "zip_code": self.user.zip_code,
                "city": self.user.city,
                "country": self.user.country,
                "password": "ich-bin-jetzt-klartext",
            },
            instance=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["password"], self.user.password)
        self.assertNotEqual(form.cleaned_data["password"], "ich-bin-jetzt-klartext")


class CustomUserCreationFormTests(TestCase):
    """
    Das Formular für neue Nutzer
    muss das Passwort korrekt hashen, nicht im Klartext speichern.
    """

    def test_creates_user_with_hashed_password(self):
        form = CustomUserCreationForm(
            data={
                "email": "newadmin@example.com",
                "first_name": "New",
                "last_name": "Admin",
                "password1": PASSWORD,
                "password2": PASSWORD,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(check_password(PASSWORD, user.password))

    def test_password_mismatch_is_rejected(self):
        form = CustomUserCreationForm(
            data={
                "email": "mismatch@example.com",
                "first_name": "New",
                "last_name": "Admin",
                "password1": PASSWORD,
                "password2": "AndereSecurePass123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class CustomUserAdminGetFieldsetsTests(TestCase):
    """
    get_fieldsets() muss die
    Berechtigungsfelder für Nicht-Superuser entfernen und für Superuser
    unverändert lassen.
    """

    @classmethod
    def setUpTestData(cls):
        cls.target = make_user(email="target@example.com")
        cls.staff_non_super = make_user(email="staff@example.com", is_staff=True)
        cls.superuser = CustomUser.objects.create_superuser(
            email="root@example.com",
            first_name="Root",
            last_name="Admin",
            password=PASSWORD,
        )

    def _fieldset_field_names(self, user):
        request = RequestFactory().get("/admin/")
        request.user = user
        user_admin = admin.site._registry[CustomUser]
        fieldsets = user_admin.get_fieldsets(request, self.target)
        return {field for _, opts in fieldsets for field in opts["fields"]}

    def test_privilege_fields_hidden_for_non_superuser(self):
        fields = self._fieldset_field_names(self.staff_non_super)

        self.assertNotIn("is_superuser", fields)
        self.assertNotIn("groups", fields)
        self.assertNotIn("user_permissions", fields)
        # Andere Felder bleiben unangetastet.
        self.assertIn("is_active", fields)
        self.assertIn("is_staff", fields)
        self.assertIn("email", fields)

    def test_privilege_fields_visible_for_superuser(self):
        fields = self._fieldset_field_names(self.superuser)

        self.assertIn("is_superuser", fields)
        self.assertIn("groups", fields)
        self.assertIn("user_permissions", fields)


class CustomUserAdminChangeViewPrivilegeEscalationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.target = make_user(email="target@example.com")

        cls.staff_non_super = make_user(email="staff@example.com", is_staff=True)
        change_perm = Permission.objects.get(
            codename="change_customuser",
            content_type=ContentType.objects.get_for_model(CustomUser),
        )
        cls.staff_non_super.user_permissions.add(change_perm)

        cls.superuser = CustomUser.objects.create_superuser(
            email="root@example.com",
            first_name="Root",
            last_name="Admin",
            password=PASSWORD,
        )

    def setUp(self):
        self.change_url = reverse(
            "admin:accounts_customuser_change", args=[self.target.pk]
        )

    def _base_post_data(self, user):
        return {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "street": user.street,
            "street_no": user.street_no,
            "zip_code": user.zip_code,
            "city": user.city,
            "country": user.country,
            "is_active": "on",
            "_save": "Save",
        }

    def test_staff_non_superuser_post_cannot_set_is_superuser(self):
        self.client.force_login(self.staff_non_super)
        data = self._base_post_data(self.target)
        data["is_superuser"] = (
            "on"  # Feld existiert im Formular nicht -> muss ignoriert werden
        )

        response = self.client.post(self.change_url, data)

        self.target.refresh_from_db()
        self.assertFalse(self.target.is_superuser)
        # 302 = Formular war gültig und wurde gespeichert (kein Validierungsfehler
        # durch fehlende Pflichtfelder, der Test prüft also tatsächlich die
        # Privilegien-Beschränkung und nicht ein zufälliges Formularscheitern).
        self.assertEqual(response.status_code, 302)

    def test_staff_non_superuser_post_cannot_add_groups_or_permissions(self):
        group = Group.objects.create(name="Testgruppe")
        extra_perm = Permission.objects.get(
            codename="delete_customuser",
            content_type=ContentType.objects.get_for_model(CustomUser),
        )

        self.client.force_login(self.staff_non_super)
        data = self._base_post_data(self.target)
        data["groups"] = [str(group.pk)]
        data["user_permissions"] = [str(extra_perm.pk)]

        response = self.client.post(self.change_url, data)

        self.target.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(list(self.target.groups.all()), [])
        self.assertEqual(list(self.target.user_permissions.all()), [])

    def test_superuser_post_can_set_is_superuser(self):
        self.client.force_login(self.superuser)
        data = self._base_post_data(self.target)
        data["is_superuser"] = "on"

        response = self.client.post(self.change_url, data)

        self.target.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.target.is_superuser)

    def test_superuser_post_can_assign_group(self):
        group = Group.objects.create(name="Testgruppe")

        self.client.force_login(self.superuser)
        data = self._base_post_data(self.target)
        data["groups"] = [str(group.pk)]

        response = self.client.post(self.change_url, data)

        self.target.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(list(self.target.groups.all()), [group])

    def test_non_superuser_cannot_escalate_own_account(self):
        # Variante des Angriffs: Staff-Nutzer versucht, sich selbst statt
        # eines fremden Kontos zum Superuser zu machen.
        self_change_url = reverse(
            "admin:accounts_customuser_change", args=[self.staff_non_super.pk]
        )
        self.client.force_login(self.staff_non_super)
        data = self._base_post_data(self.staff_non_super)
        data["is_active"] = "on"
        data["is_superuser"] = "on"

        self.client.post(self_change_url, data)

        self.staff_non_super.refresh_from_db()
        self.assertFalse(self.staff_non_super.is_superuser)


class CustomUserAdminChangeViewRenderingTests(TestCase):
    """
    Die Berechtigungsfelder für Nicht-Superuser auch im
    tatsächlich gerenderten Formular-HTML nicht auftauchen (nicht nur in
    get_fieldsets() als Datenstruktur).
    """

    @classmethod
    def setUpTestData(cls):
        cls.target = make_user(email="target@example.com")
        cls.staff_non_super = make_user(email="staff@example.com", is_staff=True)
        change_perm = Permission.objects.get(
            codename="change_customuser",
            content_type=ContentType.objects.get_for_model(CustomUser),
        )
        cls.staff_non_super.user_permissions.add(change_perm)

    def test_change_form_get_omits_is_superuser_field_for_non_superuser(self):
        self.client.force_login(self.staff_non_super)
        url = reverse("admin:accounts_customuser_change", args=[self.target.pk])

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        adminform = response.context["adminform"]
        self.assertNotIn("is_superuser", adminform.form.fields)
        self.assertNotIn("groups", adminform.form.fields)
        self.assertNotIn("user_permissions", adminform.form.fields)
