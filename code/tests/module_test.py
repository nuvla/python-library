from unittest import TestCase

from nuvla.api.resources.module import (ModuleBuilder, AppBuilderK8s,
                                        AppBuilderDocker)


class ModuleBuilderTest(TestCase):

    def test_minimal_build(self):
        mb = ModuleBuilder()
        self.assertRaises(Exception, mb.build)

        mb.path('path')
        try:
            mb.build()
        except Exception as ex:
            if ModuleBuilder._type_not_set_err != str(ex):
                self.fail('build() should have failed with {}'
                          .format(ModuleBuilder._type_not_set_err))

        mb.name('hello').description('world')
        test_m = {
            'parent-path': '',
            'path': 'path',
            'name': 'hello',
            'description': 'world'}
        self.assertEqual(mb.module, test_m)


class AppBuilderK8sTest(TestCase):

    def test_path_test(self):
        mb = AppBuilderK8s()

        mb.path('path')
        self.assertEqual(mb.module['path'], 'path')
        self.assertEqual(mb.module['parent-path'], '')

        mb.path('path/sub-path')
        self.assertEqual(mb.module['path'], 'path/sub-path')
        self.assertEqual(mb.module['parent-path'], 'path')

    def test_minimal_build(self):
        mb = AppBuilderK8s()
        self.assertRaises(Exception, mb.build)

        mb.path('path')
        self.assertRaises(Exception, mb.build)

        mb.script('script')
        mb.commit('message')
        module = mb.build()

        test_m = {
            'parent-path': '',
            'path': 'path',
            'content': {
                AppBuilderK8s.script_key: 'script',
                'commit': 'message'},
            'name': 'path',
            'description': 'path',
            'subtype': AppBuilderK8s.type
        }
        self.assertEqual(module, test_m)


class AppBuilderDockerTest(TestCase):

    def test_minimal_build(self):
        mb = AppBuilderDocker()
        self.assertRaises(Exception, mb.build)

        mb.path('path')
        self.assertRaises(Exception, mb.build)

        mb.script('script')
        mb.commit('message')
        module = mb.build()

        test_m = {
            'parent-path': '',
            'path': 'path',
            'content': {
                AppBuilderDocker.script_key: 'script',
                'commit': 'message'},
            'name': 'path',
            'description': 'path',
            'subtype': AppBuilderDocker.type
        }
        self.assertEqual(module, test_m)
