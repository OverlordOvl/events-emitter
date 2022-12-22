import unittest

from eventemitter.emitter import EventEmitter
from eventemitter.emitter_types.emitter_dataclasess.callback_dataclasses import CallbackData
from mock.mock_events import BaseTestEnum


class TestAsyncEmitterMethods(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.emitter = EventEmitter()

    async def test_async_on_emit(self):
        value = {'touched': False}

        async def touch_value():
            value['touched'] = True

        self.emitter.on(BaseTestEnum.TestKey1, touch_value)
        await self.emitter.async_emit(BaseTestEnum.TestKey1)
        self.assertTrue(value['touched'])

    async def test_async_on_emit_with_args(self):
        value = {'touched': False}

        async def touch_value(arg):
            value['touched'] = arg

        self.emitter.on(BaseTestEnum.TestKey1, touch_value)
        await self.emitter.async_emit(BaseTestEnum.TestKey1, True)
        self.assertTrue(value['touched'])

    async def test_async_on_emit_with_kwargs(self):
        value = {'touched': False}

        async def touch_value(**kwargs):
            value['touched'] = kwargs['arg']

        self.emitter.on(BaseTestEnum.TestKey1, touch_value)
        await self.emitter.async_emit(BaseTestEnum.TestKey1, arg=True)
        self.assertTrue(value['touched'])

    async def test_async_on_emit_with_args_and_kwargs(self):
        value = {'touched': False}

        async def touch_value(is_true, **kwargs):
            value['touched'] = is_true and kwargs['arg']

        self.emitter.on(BaseTestEnum.TestKey1, touch_value)
        await self.emitter.async_emit(BaseTestEnum.TestKey1, True, arg=True)
        self.assertTrue(value['touched'])


class TestEmitterMethods(unittest.TestCase):
    def setUp(self) -> None:
        self.emitter = EventEmitter()

    def test_on(self):
        self.emitter.on(BaseTestEnum.TestKey1, lambda: ...)
        self.emitter.on(BaseTestEnum.TestKey2, lambda: ...)

        self.assertEqual(
            self.emitter._get_events_keys(),
            [BaseTestEnum.TestKey1, BaseTestEnum.TestKey2],
        )

    def test_once(self):
        self.emitter.once(BaseTestEnum.TestKey1, lambda: ...)
        self.emitter.once(BaseTestEnum.TestKey2, lambda: ...)

        self.assertEqual(
            self.emitter._get_once_keys(),
            [BaseTestEnum.TestKey1, BaseTestEnum.TestKey2],
        )

    def test_on_emit(self):
        value = {'touched': False}

        def touch_value():
            value['touched'] = True

        self.emitter.on(BaseTestEnum.TestKey1, touch_value)
        self.assertEqual(value['touched'], False)
        self.emitter.emit(BaseTestEnum.TestKey1)
        self.assertEqual(value['touched'], True)

    def test_once_emit(self):
        calls_count = {'calls': 0}

        def increment_calls_count():
            calls_count['calls'] += 1

        self.emitter.once(BaseTestEnum.TestKey1, increment_calls_count)
        self.emitter.emit(BaseTestEnum.TestKey1)
        self.emitter.emit(BaseTestEnum.TestKey1)
        self.assertEqual(calls_count['calls'], 1)

    def test_subscribe(self):
        callback = CallbackData(lambda: None)
        self.emitter.on(BaseTestEnum.TestKey1, callback)
        self.emitter.once(BaseTestEnum.TestKey1, callback)
        self.assertDictEqual(
            self.emitter._get_events(), {BaseTestEnum.TestKey1: [callback]}
        )
        self.assertDictEqual(
            self.emitter._get_once(), {BaseTestEnum.TestKey1: [callback]}
        )

    def test_get_keys(self):
        self.emitter.on(BaseTestEnum.TestKey1, lambda: ...)
        self.emitter.once(BaseTestEnum.TestKey1, lambda: ...)
        self.assertEqual(self.emitter._get_events_keys(), [BaseTestEnum.TestKey1])
        self.assertEqual(self.emitter._get_once_keys(), [BaseTestEnum.TestKey1])

    def test_remove(self):
        self.emitter.on(BaseTestEnum.TestKey1, lambda: ...)
        self.emitter.on(BaseTestEnum.TestKey2, lambda: ...)
        self.emitter.once(BaseTestEnum.TestKey1, lambda: ...)
        self.emitter.once(BaseTestEnum.TestKey2, lambda: ...)
        self.emitter.remove(BaseTestEnum.TestKey1)
        self.assertEqual(self.emitter._get_events_keys(), [BaseTestEnum.TestKey2])
        self.assertEqual(self.emitter._get_once_keys(), [BaseTestEnum.TestKey2])

    def test_clear(self):
        for i in range(100):
            self.emitter.on(f'Event№{i}', lambda: ...)
            self.emitter.once(f'Event№{i}', lambda: ...)
        self.emitter.clear()
        self.assertEqual(self.emitter._get_events_keys(), [])
        self.assertEqual(self.emitter._get_once_keys(), [])

    def tearDown(self) -> None:
        self.emitter.clear()


if __name__ == '__main__':
    unittest.main()
