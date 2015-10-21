angular
  .module('refineryApp')
  .factory('authService', ['$q', '$resource', 'settings', 'sessionService',
    function ($q, $resource, settings, sessionService) {
      var auth = {},
          authLastCheck = 0;

      /**
       * Check whether a user is authenticated or not.
       *
       * @method  checkUserStatus
       * @author  Fritz Lekschas
       * @date    2015-10-21
       *
       * @return  {Object}  Angular promise
       */
      function checkUserStatus () {
        var query = $resource(
              settings.appRoot + settings.refineryApi + '/user_authentication/',
              {
                format: 'json'
              },
              {
                query: {
                  method: 'GET',
                  isArray: false,
                }
              }
            ).query();

        return query.$promise;
      }

      /**
       * Creates a new user session
       *
       * @method  createSession
       * @author  Fritz Lekschas
       * @date    2015-10-21
       *
       * @return  {Object}  Angular promise resolving the session.
       */
      function createSession () {
        var userStatus = checkUserStatus();

        return userStatus
          .then(function (response) {
            sessionService.create({
              userId: response.id,
              isAdmin: response.is_admin,
            });
          });
      }

      /**
       * Checks whether the current user is an adminitrator.
       *
       * @method  isAdmin
       * @author  Fritz Lekschas
       * @date    2015-10-21
       *
       * @return  {Boolean}  `true` if the current user is an adminitrator.
       */
      auth.isAdmin = function () {
        var now = new Date().getTime(),
            session;

        if (now - sessionService.get('date') > settings.authThrottling) {
          session = createSession();
        } else {
          session = $q.when();
        }

        return session.then(
          // Success
          function () {
            return sessionService.get('isAdmin');
          }
        );
      };

      /**
       * Check whether the current user is authenticated.
       *
       * @method  isAuthenticated
       * @author  Fritz Lekschas
       * @date    2015-10-21
       *
       * @return  {Boolean}  `true` if the current user is authenticaed.
       */
      auth.isAuthenticated = function () {
        var now = new Date().getTime(),
            session;

        if (now - sessionService.get('date') > settings.authThrottling) {
          session = createSession();
        } else {
          session = $q.when();
        }

        return session.then(
          // Success
          function () {
            return sessionService.get('userId') >= 0;
          }
        );
      };

      return auth;
    }
  ]);
