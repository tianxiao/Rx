from rx.observable import Observable, ObservableMeta
from rx.anonymousobservable import AnonymousObservable

from rx.disposables import Disposable, CompositeDisposable
from rx.concurrency import immediate_scheduler, current_thread_scheduler

class ObservableCreation(Observable, metaclass=ObservableMeta):

    @classmethod
    def create(cls, subscribe):
        def _subscribe(observer):
            return Disposable(subscribe(observer))
        
        return AnonymousObservable(_subscribe)

    @classmethod
    def create_with_disposable(cls, subscribe):
        return AnonymousObservable(subscribe)

    @classmethod
    def defer(cls, observable_factory):
        """Returns an observable sequence that invokes the specified factory 
        function whenever a new observer subscribes.
     
        1 - res = rx.Observable.defer(lambda: rx.Observable.from_array([1,2,3]))    
    
        observable_factory -- Observable factory function to invoke for each 
            observer that subscribes to the resulting sequence.
    
        Returns an observable sequence whose observers trigger an invocation 
        of the given observable factory function.
        """

        def subscribe(observer):
            result = None
            try:
                result = observable_factory()
            except Exception as ex:
                return Observable.throw_exception(ex).subscribe(observer)
            
            return result.subscribe(observer)
        return AnonymousObservable(subscribe)

    @classmethod
    def empty(cls, scheduler=None):
        """Returns an empty observable sequence, using the specified scheduler 
        to send out the single OnCompleted message.
     
        1 - res = rx.Observable.empty()
        2 - res = rx.Observable.empty(Rx.Scheduler.timeout)
    
        scheduler -- Scheduler to send the termination call on.
    
        returs an observable sequence with no elements.
        """

        scheduler = scheduler or immediate_scheduler
    
        def subscribe(observer):
            def action(scheduler, state):
                observer.on_completed()

            return scheduler.schedule(action)
        return AnonymousObservable(subscribe)

    @classmethod
    def from_array(cls, array, scheduler):
        """Converts an array to an observable sequence, using an optional 
        scheduler to enumerate the array.
    
        1 - res = rx.Observable.from_array([1,2,3])
        2 - res = rx.Observable.from_array([1,2,3], rx.Scheduler.timeout)
     
        Keyword arguments:
        scheduler -- [Optional] Scheduler to run the enumeration of the input sequence on.
     
        Returns the observable sequence whose elements are pulled from the 
        given enumerable sequence.
        """

        scheduler = scheduler or current_thread_scheduler

        def subscribe(observer):
            count = 0
            
            def action(action1, state=None):
                nonlocal count
                
                if count < len(array):
                    observer.on_next(array[count])
                    count += 1
                    action1(action)
                else:
                    observer.on_completed()
                
            return scheduler.schedule_recursive(action)
        return AnonymousObservable(subscribe)

    @classmethod
    def generate(cls, initial_state, condition, iterate, result_selector, scheduler=None):
        """Generates an observable sequence by running a state-driven loop 
        producing the sequence's elements, using the specified scheduler to 
        send out observer messages.
     
        1 - res = rx.Observable.generate(0, function (x) { return x < 10; }, function (x) { return x + 1; }, function (x) { return x; });
        2 - res = rx.Observable.generate(0, function (x) { return x < 10; }, function (x) { return x + 1; }, function (x) { return x; }, Rx.Scheduler.timeout);
        
        Keyword arguments:
        initial_state -- Initial state.
        condition -- Condition to terminate generation (upon returning false).
        iterate -- Iteration step function.
        result_selector -- Selector function for results produced in the sequence.
        scheduler -- [Optional] Scheduler on which to run the generator loop. 
            If not provided, defaults to CurrentThreadScheduler.
    
        Returns the generated sequence.
        """

        scheduler = scheduler or current_thread_scheduler

        def subscribe(observer):
            first = True
            state = initial_state
            
            def action (action1, state1=None):
                nonlocal first, state
                has_result = False
                result = None

                try:
                    if first:
                        first = False
                    else:
                        state = iterate(state)
                    
                    has_result = condition(state)
                    if has_result:
                        result = result_selector(state)
                    
                except Exception as exception:
                    observer.on_error(exception)
                    return
                
                if has_result:
                    observer.on_next(result)
                    action1()
                else:
                    observer.on_completed()
                
            return scheduler.schedule_recursive(action)
        return AnonymousObservable(subscribe)
    
    @classmethod
    def never(cls):
        """Returns a non-terminating observable sequence, which can be used to 
        denote an infinite duration (e.g. when using reactive joins).
     
        Returns an observable sequence whose observers will never get called.
        """
        def subscribe(observer):
            return Disposable.empty()

        return AnonymousObservable(subscribe)

    @classmethod
    def range(cls, start, count, scheduler=None):
        """Generates an observable sequence of integral numbers within a 
        specified range, using the specified scheduler to send out observer 
        messages.
     
        1 - res = Rx.Observable.range(0, 10);
        2 - res = Rx.Observable.range(0, 10, Rx.Scheduler.timeout);
    
        Keyword arguments:
        start -- The value of the first integer in the sequence.
        count -- The number of sequential integers to generate.
        scheduler -- [Optional] Scheduler to run the generator loop on. If not 
            specified, defaults to Scheduler.currentThread.
    
        Returns an observable sequence that contains a range of sequential 
        integral numbers.
        """
        scheduler = scheduler or current_thread_scheduler
        
        def subscribe(observer):
            def action(scheduler, i):
                #print("Observable:range:subscribe:action", scheduler, i)
                if i < count:
                    observer.on_next(start + i)
                    scheduler(i + 1)
                else:
                    #print "completed"
                    observer.on_completed()
                
            return scheduler.schedule_recursive(action, 0)
        return AnonymousObservable(subscribe)

    @classmethod
    def repeat(cls, value=None, repeat_count=None, scheduler=None):
        """Generates an observable sequence that repeats the given element the 
        specified number of times, using the specified scheduler to send out 
        observer messages.
    
        1 - res = Rx.Observable.repeat(42)
        2 - res = Rx.Observable.repeat(42, 4)
        3 - res = Rx.Observable.repeat(42, 4, Rx.Scheduler.timeout)
        4 - res = Rx.Observable.repeat(42, None, Rx.Scheduler.timeout)
    
        Keyword arguments:
        value -- Element to repeat.
        repeat_count -- [Optiona] Number of times to repeat the element. If not 
            specified, repeats indefinitely.
        scheduler -- Scheduler to run the producer loop on. If not specified, 
            defaults to ImmediateScheduler.
    
        Returns an observable sequence that repeats the given element the 
        specified number of times.
        """

        scheduler = scheduler or current_thread_scheduler
        if repeat_count == -1:
            repeat_count = None
        
        xs = cls.return_value(value, scheduler)
        ret = xs.repeat(repeat_count)
        return ret

    @classmethod
    def return_value(cls, value, scheduler=None):
        scheduler = scheduler or immediate_scheduler

        def subscribe(observer):
            def action(scheduler, state=None):
                observer.on_next(value)
                observer.on_completed()

            return scheduler.schedule(action)
        return AnonymousObservable(subscribe)

    @classmethod
    def throw_exception(cls, exception, scheduler=None):
        """Returns an observable sequence that terminates with an exception, 
        using the specified scheduler to send out the single OnError message.
    
        1 - res = rx.Observable.throw_exception(new Error('Error'));
        2 - res = rx.Observable.throw_exception(new Error('Error'), Rx.Scheduler.timeout);
     
        Keyword arguments:
        exception -- An object used for the sequence's termination.
        scheduler -- Scheduler to send the exceptional termination call on. If
            not specified, defaults to ImmediateScheduler.
    
        Returns the observable sequence that terminates exceptionally with the 
        specified exception object.
        """
        scheduler = scheduler or immediate_scheduler
        
        exception = Exception(exception) if type(exception) is Exception else exception

        def subscribe(observer):
            def action(scheduler, state):
                observer.on_error(exception)

            return scheduler.schedule(action)
        return AnonymousObservable(subscribe)

    @classmethod
    def using(cls, resource_factory, observable_factory):
        """Constructs an observable sequence that depends on a resource object,
        whose lifetime is tied to the resulting observable sequence's lifetime.
      
        1 - res = Rx.Observable.using(function () { return new AsyncSubject(); }, function (s) { return s; });
    
        Keyword arguments:
        resource_factory -- Factory function to obtain a resource object.
        observable_factory -- Factory function to obtain an observable sequence
            that depends on the obtained resource.
     
        Returns an observable sequence whose lifetime controls the lifetime of 
        the dependent resource object.
        """
        def subscribe(observer):
            disposable = Disposable.empty()
            try:
                resource = resource_factory()
                if resource:
                    disposable = resource
                
                source = observable_factory(resource)
            except Exception as exception:
                d = Observable.throw_exception(exception).subscribe(observer)
                return CompositeDisposable(d, disposable)
            
            return CompositeDisposable(source.subscribe(observer), disposable)
        return AnonymousObservable(subscribe)
