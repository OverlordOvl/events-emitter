import asyncio
from asyncio import AbstractEventLoop
from collections import defaultdict
from typing import Any, Awaitable, Callable, List

from .emitter_types.emitter_dataclasess.callback_dataclasses import CallbackData
from .emitter_types.emitter_dataclasess.event_dataclasses import EventCallback
from .emitter_types.enums.base_enum import BaseEnum
from .emitter_types.type_aliases import Callback, Event, EventsStorage


async def _try_catch_coro(
    emitter: "EventEmitter", event: Event, callback: Callback, coro: Awaitable
):
    """
    The _try_catch_coro function is a helper function that wraps coroutines in
    a try/catch block. If an exception is caught the function will use the events_emitter
    to emit the failure event. If, however, the current event _is_ the failure event then
    the method reraises. The reraised exception may show in debug mode for the
    event loop but is otherwise silently dropped.

    :param emitter:"EventEmitter": Call the emit method
    :param event:Event: Pass the event that triggered the
    :param callback:Callback: Provide the coroutine with a
    :param coro:Awaitable: Pass the coroutine that should be
    :return: The coroutine object
    """
    try:
        await coro
    except Exception as exc:
        if event == emitter.LISTENER_ERROR_EVENT:
            raise exc
        emitter.emit(emitter.LISTENER_ERROR_EVENT, event, callback, exc)


class EventEmitter:
    LISTENER_ERROR_EVENT: Event = "listener-error"

    def __init__(self, loop: AbstractEventLoop = None):
        self.__events: EventsStorage = defaultdict(list)
        self.__once: EventsStorage = defaultdict(list)
        self._loop = loop or asyncio.new_event_loop()

    def on(
        self,
        event: Event,
        callback: Callback,
        *callback_args: Any,
        **callback_kwargs: Any,
    ):
        """
        The on function is used to register a callback function for an event.
        It takes the following arguments:
            - event: The name of the event to register a callback for. This can be any string, but it is recommended that you use something
            like "on_<event>". For example, if you want to listen for when an object has been added, you would pass
            "on_object_added" as your argument.
            - callback: The function that should be called when the specified event occurs. It must take at least one argument
             (the object that triggered the event), and may also take additional positional and keyword arguments

        :param self: Access the object's attributes from inside the callback
        :param event:Event: Specify the event that is being registered
        :param callback:Callback: Define the function that will be called when the event is fired
        :param callback_args:Any: Pass a variable number of arguments to the callback function
        :param callback_kwargs:Any: Pass in any additional keyword arguments to the callback function
        :return: The event that was just registered
        """
        self._register_event(
            self.__events, event, callback, callback_args, callback_kwargs
        )

    def once(
        self,
        event: Event,
        callback: Callback,
        *callback_args: Any,
        **callback_kwargs: Any,
    ):
        """
        The once function allows you to register an event callback
        that will only be called once, and then automatically unregistered.


        :param self: Access the attributes of the class
        :param event:Event: Specify the event that will trigger the callback
        :param callback:Callback: Specify the function to be called when the event is fired
        :param callback_args:Any: Pass in arguments to the callback function
        :param callback_kwargs:Any: Pass in any keyword arguments that are needed by the callback function
        :return: A function that wraps the callback
        """
        self._register_event(
            self.__once, event, callback, callback_args, callback_kwargs
        )

    def emit(self, event: Event, *callback_args: Any, **callback_kwargs: Any):
        """
        The emit function is used to dispatch an event.
        It accepts an Event object, and any number of positional and keyword arguments.
        The event will be dispatched to all listeners that are registered for the given event type.

        :param self: Access the state of the object
        :param event:Event: Pass the event that is being emitted
        :param callback_args:Any: Pass a list of arguments to the callback function
        :param callback_kwargs:Any: Pass in any additional keyword arguments that are needed to be passed into the callback function
        :return: None
        """
        event_instance = EventCallback(event, callback_args, callback_kwargs)
        for collection in self._dispatch(event_instance):
            if not collection:
                continue
            self._process_collection(collection, event_instance)

    async def async_emit(
        self, event: Event, *callback_args: Any, **callback_kwargs: Any
    ):
        """
        The async_emit function is used to async dispatch an event.
        It accepts an Event object, and any number of positional and keyword arguments.
        The event will be dispatched to all listeners that are registered for the given event type.

        :param self: Access the state of the object
        :param event:Event: Pass the event that is being emitted
        :param callback_args:Any: Pass a list of arguments to the callback function
        :param callback_kwargs:Any: Pass in any additional keyword arguments that are needed to be passed into the callback function
        :return: None
        """
        event_instance = EventCallback(event, callback_args, callback_kwargs)
        await asyncio.gather(
            *[
                self.async_process_collection(collection, event_instance)
                for collection in self._dispatch(event_instance)
                if collection
            ]
        )

    def remove(self, event: BaseEnum, _collection: EventsStorage = None):
        """
        The remove function removes an event from the events dictionary.
        If the collection parameter is not None, it will remove that event from that collection only.
        Otherwise, it will remove all instances of that event in both collections.


        :param self: Access the class attributes
        :param event:BaseEnum: Specify the event to remove
        :param _collection:EventsStorage=None: Specify the collection to remove from
        :return: None
        """
        if _collection is not None:
            _collection.pop(event, None)
            return
        self.__events.pop(event, None)
        self.__once.pop(event, None)

    def clear(self):
        """
        The clear function clears all events from the event dictionary.

        :param self: Refer to the object itself
        :return: None
        """
        self.__events.clear()
        self.__once.clear()

    def _register_event(
        self,
        storage: EventsStorage,
        event: Event,
        callback: Callback,
        callback_args: Any,
        callback_kwargs: Any,
    ):
        """
        The _register_event function is a helper function that registers an event with the given storage.
        It takes in the following parameters:
            * self - The object instance of this class (self)
            * storage - The EventsStorage object to register the event with. This will be either self._events or self._once_events,
            depending on whether it's an "on" or "once" callback respectively.
            * event - The name of the Event to register for (string)
            * callback - A reference to a callable function/object that should be called when said Event occurs (callable)

        :param self: Access the instance of the class that contains it
        :param storage:EventsStorage: Store the event and its corresponding callbacks
        :param event:Event: Specify the event that is being registered
        :param callback:Callback: Specify the function that should be called when the event is triggered
        :param callback_args:Any: Pass a list of arguments to the callback function
        :param callback_kwargs:Any: Pass additional parameters to the callback function
        :param : Store the event in a dictionary
        :return: A list of callbacks for a given event
        """
        storage[event].append(
            self._convert_to_callback(
                callback=callback,
                callback_args=callback_args,
                callback_kwargs=callback_kwargs,
            )
        )

    def _dispatch(self, event: EventCallback) -> List[List[CallbackData | None]]:
        """
        The _dispatch function is a private function that dispatches an event to all
        registered callbacks. It does this by first checking the __once collection for
        any registered callbacks, and then it checks the __events collection for any
        registered callbacks. If there are no registered events, it will return False.

        :param self: Reference the object that is calling the function
        :param event:EventCallback: Pass the event to the function that is called when it is dispatched
        """
        return [
            self._dispatch_collection(self.__once, event, disposable_event=True),
            self._dispatch_collection(self.__events, event),
        ]

    def _dispatch_collection(
        self,
        collection: EventsStorage,
        event: Event,
        disposable_event=False,
    ):
        if not (callbacks := collection.get(event.event_name)):
            return

        if disposable_event:
            self.remove(event.event_name, _collection=collection)

        return callbacks

    async def async_process_collection(
        self, callbacks: List[CallbackData], event: Event
    ):
        tasks = []
        for callback in callbacks:
            callback_args = [*event.callback_args, *callback.callback_args]
            callback_kwargs = {**{**event.callback_kwargs, **callback.callback_kwargs}}
            tasks.append(
                asyncio.create_task(
                    self._dispatch_coroutine(
                        event, callback.callback, *callback_args, **callback_kwargs
                    )
                )
            )

        await asyncio.gather(*tasks)

    def _process_collection(self, callbacks: List[CallbackData], event: Event):
        """
        The _dispatch_collection function is a helper function that dispatches the event to all callbacks in the collection.
        It takes an EventsStorage object and an Event as arguments. It then iterates through each callback in the collection,
        and checks if it's a coroutine or partial function (which are both valid for asyncio). If it is, then we dispatch to
        the _dispatch_coroutine function which will run this coroutine with the given args and kwargs. Otherwise, we dispatch
        to _dispatch_functions which will run this callback with its given args and kwargs.

        :param self: Access the class attributes
        :param event:Event: Pass the event that is being dispatched to the callback
        :return: The result of the _dispatch_coroutine function if the callback is a coroutine, or else it returns the result of the
        _dispatch_functon
        """
        for callback in callbacks:
            callback_args = [*event.callback_args, *callback.callback_args]
            callback_kwargs = {**{**event.callback_kwargs, **callback.callback_kwargs}}

            self._dispatch_function(
                event, callback.callback, *callback_args, **callback_kwargs
            )

    async def _dispatch_coroutine(
        self,
        event: Event,
        callback: Callable,
        *callback_args: Any,
        **callback_kwargs: Any,
    ):
        """
        The _dispatch_coroutine function is a helper function that dispatches the callback
        to an event loop. It also handles errors thrown by the callback, and ensures that
        the coroutine is closed after it has been dispatched to the event loop. The _dispatch_coroutine
        is called from within :meth:`~asyncio_event_loops.AsyncioEventLoops._dispatch`. This allows for
        a single point of entry when dispatching callbacks to an event loop.

        :param self: Access the eventemitter object
        :param event:Event: Pass the event that triggered the callback
        :param callback:Callable: Call the coroutine
        :param *callback_args:Any: Pass arguments to the callback function
        :param **callback_kwargs:Any: Pass keyword arguments to the callback function
        :return: None
        """
        try:
            coro = callback(*callback_args, **callback_kwargs)
        except Exception as exc:
            if event == self.LISTENER_ERROR_EVENT:
                raise
            self.emit(self.LISTENER_ERROR_EVENT, event, callback, exc)
            return

        await _try_catch_coro(self, event, callback, coro)

    def _dispatch_function(
        self,
        event: Event,
        callback: Callback,
        *callback_args: Any,
        **callback_kwargs: Any,
    ):
        """
        The _dispatch_function function is a helper function that dispatches the event to the callback.
        It also handles errors if they occur during execution of the callback. If an error occurs, it will
        either be raised or emitted as a listener error depending on whether it occurred in an event handler
        or not.

        :param self: Access the object instance that is associated with the listener
        :param event:Event: Pass the event that was fired to the callback
        :param callback:Callback: Call the callback function that was passed to the event events_emitter
        :param callback_args:Any: Pass the arguments that are passed to the callback function
        :param callback_kwargs:Any: Pass any additional arguments that are passed to the callback function
        :return: The result of the callback function
        """
        try:

            return callback(*callback_args, **callback_kwargs)

        except Exception as exc:

            if event == self.LISTENER_ERROR_EVENT:
                raise

            return self.emit(self.LISTENER_ERROR_EVENT, event, callback, exc)

    @staticmethod
    def _convert_to_callback(
        callback: Callback, callback_args: Any, callback_kwargs: Any
    ) -> CallbackData:
        """
        The _convert_to_callback function is used to convert a callback function, its arguments, and
        keyword arguments into a CallbackData object. This allows the callback to be called in the main
        loop without needing to pass it through multiple functions. The _convert_to_callback function is
        used by all methods that add callbacks.

        :param callback:Callback: Specify the callback function that should be called when the button is clicked
        :param callback_args:Any: Pass arguments to the callback
        :param callback_kwargs:Any: Pass keyword arguments to the callback function
        :return: A CallbackData object
        """
        return (
            callback
            if isinstance(callback, CallbackData)
            else CallbackData(callback, callback_args, callback_kwargs)
        )

    def _get_events(self) -> EventsStorage:
        """
        The _get_events function is a helper function that returns the EventsStorage object
        that stores all events that have been fired. This allows for other functions to
        access this storage and iterate over it, if necessary.

        :param self: Access the attributes and methods of the class
        :return: The self
        """
        return self.__events

    def _get_once(self) -> EventsStorage:
        """
        The _get_once function is a helper function that returns the EventsStorage object
        that stores all events that have been fired. This allows for other functions to
        access this storage and iterate over it, if necessary.

        :param self: Access the attributes and methods of the class
        :return: The self
        """
        return self.__once

    def _get_events_keys(self) -> List[Event]:
        """
        The _get_events_keys function returns a list of all the events that have been
        added to the queue and are waiting to be processed.

        :param self: Access variables that belongs to the class
        :return: A list of all the events that are in the event dictionary
        """
        return list(self.__events)

    def _get_once_keys(self) -> List[Event]:
        """
        The _get_once_keys function returns a list of all the events that have been
        added to the queue and are waiting to be processed.

        :param self: Access the class attributes
        :return: A list of the events that have been added to the queue and are waiting to be executed
        """
        return list(self.__once)
