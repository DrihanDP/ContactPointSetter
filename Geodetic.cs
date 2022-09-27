////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// <copyright file="Geodetic.cs" company="Racelogic">
// (c) Racelogic Limited 2014
// </copyright>
// <author>Darran Shepherd</author>
// <date>15/10/2013</date>
// <summary>Implements the Geodetic class</summary>
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using System.Text.RegularExpressions;
using Flitesys.GeographicLib;
using Newtonsoft.Json;
using Racelogic.Maths;
using static System.FormattableString;

namespace Racelogic.Geodetics
{
    ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    /// <summary>   The geographical coordinates expressed as Latitude, Longitude and Altitude. </summary>
    ///
    /// <remarks>   Darran Shepherd, 15/10/2013. </remarks>
    ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

    [JsonObject(MemberSerialization.OptIn)]
    [DebuggerDisplay("Lat: {Latitude / System.Math.PI * 180.0}°   Long: {Longitude / System.Math.PI * 180.0}°   Alt: {Altitude}m")]
    public readonly struct Geodetic
    {
        #region TEST

        ////Geodesic test

        ////JFK to LHR
        //Geodetic g1 = Geodetic.FromDegrees(40.639801, -73.7789002, 0.0);
        //Geodetic g2 = Geodetic.FromDegrees(51.4706001, -0.461941, 0.0);
        //double expectedDistance = 5554539.948955708;
        //double expectedHeading = 0.89677881055989319;

        //////JFK to CAN(nearly antipodal)
        ////Geodetic g1 = Geodetic.FromDegrees(40.639801, -73.7789002, 0.0);
        ////Geodetic g2 = Geodetic.FromDegrees(23.3924007, 113.2990036, 0.0);
        ////double expectedDistance = 12877835.864286377;
        ////double expectedHeading = -0.12535315402217994;

        //double distance = g1.SurfaceDistance(g2, out double heading);
        //double diffDistance = Math.Abs(distance - expectedDistance);
        //    if (diffDistance > 5e-9) //5nm
        //        throw new Exception("SurfaceDistance failed!");
        //double diffHeading = Math.Abs(heading - expectedHeading);
        //    if (diffHeading > 5e-9 / Datum.WGS84.SemiMajorAxis) //5nm over Earth radius
        //        throw new Exception("SurfaceDistance heading failed!");
        //Geodetic gg2 = g1.SurfaceTravel(heading, distance);
        //double diffLat = Math.Abs(gg2.Latitude - g2.Latitude);
        //double diffLong = Math.Abs(gg2.Longitude - g2.Longitude);
        //double diffRadians = Math.Sqrt(diffLat * diffLat + diffLong * diffLong);
        //double diffMetres = diffRadians * Datum.WGS84.SemiMajorAxis;
        //    if (diffMetres > 5e-9) //5nm
        //        throw new Exception("SurfaceDistance-SurfaceTravel round trip failed!");

        #endregion TEST

        #region Private declarations

        /// <summary>   The decimal value of PI. </summary>
        private const decimal PIm = 3.141592653589793238462643383279502884m;

        /// <summary>   The conversion factor from degrees to radians in decimal. </summary>
        internal const decimal D2Rm = PIm / 180.0m;

        /// <summary>   The conversion factor from radians to degrees in decimal. </summary>
        internal const decimal R2Dm = 180.0m / PIm;

        /// <summary>   The conversion factor from degrees to radians. </summary>
        internal const double D2R = (double)D2Rm;

        /// <summary>   The conversion factor from radians to degrees. </summary>
        internal const double R2D = (double)R2Dm;

        /// <summary>   A culture using comma as a decimal separator. </summary>
        private static readonly CultureInfo commaCulture = CultureInfo.GetCultureInfo("de");

        private static readonly Dictionary<Datum, Geodesic> geodesicLibrary = new();

        private static Regex parseNumbersRegex;

        #endregion Private declarations

        #region Public declarations

        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Gets the latitude in radians.  North is positive. </summary>
        ///
        /// <value> The latitude in radians. </value>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        [JsonProperty(PropertyName = "Latitude")]
        public readonly double Latitude;



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Gets the longitude in radians.  Range: ˂-PI, PI).  East is positive. </summary>
        ///
        /// <value> The longitude in radians. </value>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        [JsonProperty(PropertyName = "Longitude")]
        public readonly double Longitude;



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Gets the altitude in metres. </summary>
        ///
        /// <value> The altitude in metres. </value>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        [JsonProperty(PropertyName = "Altitude")]
        public readonly double Altitude;

        #endregion Public declarations

        #region Constructors

        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   The geographical coordinates expressed as Latitude, Longitude and Altitude. </summary>
        ///
        /// <remarks>   Darran Shepherd, 15/10/2013. </remarks>
        ///
        /// <param name="latitude">     The latitude in radians. </param>
        /// <param name="longitude">    The longitude in radians. </param>
        /// <param name="altitude">     The altitude in metres. </param>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        [JsonConstructor]
        public Geodetic(double latitude, double longitude, double altitude)
        {
            Latitude = latitude;
            Longitude = FastMath.NormalizeRadiansPi(longitude);
            Altitude = altitude;
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   The geographical coordinates expressed as Latitude, Longitude and Altitude. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 12/07/2019. </remarks>
        ///
        /// <param name="latitude">     The latitude in radians. </param>
        /// <param name="longitude">    The longitude in radians. </param>
        /// <param name="altitude">     The altitude in metres. </param>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public Geodetic(decimal latitude, decimal longitude, double altitude)
        {
            Latitude = (double)latitude;
            Longitude = (double)FastMath.NormalizeRadiansPi(longitude);
            Altitude = altitude;
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   A type deconstructor that extracts the individual members from this object. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 24/01/2020. </remarks>
        ///
        /// <returns>   A Tuple with latitude [rad], longitude [rad] and altitude [m]. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public (double Latitude, double Longitude, double Altitude) Deconstruct()
        {
            return (Latitude, Longitude, Altitude);
        }

        #endregion Constructors

        #region Properties

        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Gets the compiled RegEx which can be used to split coordinate strings into an array of numbers. </summary>
        ///
        /// <value> The RegEx.  It is never null. </value>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        private static Regex ParseNumbersRegex
        {
            get
            {
                if (parseNumbersRegex is null)
                {
                    string separator = CultureInfo.CurrentCulture.NumberFormat.NumberDecimalSeparator;
                    string regexString = (separator == "." || separator == ",") ? @"-?\d+([\.\,]\d+)?" : $@"-?\d+([\.\,\{separator}]\d+)?";
                    parseNumbersRegex = new Regex(regexString, RegexOptions.Compiled);
                }

                return parseNumbersRegex;
            }
        }

        #endregion Properties

        #region Methods

        #region Geodesic

        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Calculates the end point of travel along the surface of an ellipsoid, from current location over the specified distance, in the direction of
        ///             the specified initial heading.  
        ///             It uses the Charles F.F. Karney algorithm published in "Algorithms for geodesics" and implemented in NETGeographicLib.  
        ///             Accuracy is normally better than 1nm. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 13/05/2019. </remarks>
        ///
        /// <param name="initialHeading">   The initial heading in radians. </param>
        /// <param name="distance">         The distance in metres. </param>
        /// <param name="datum">            [Optional] The geodetic datum.  Null means WGS84.  
        ///                                 Default value: null. </param>
        ///
        /// <returns>   A geodetic location. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public Geodetic SurfaceTravel(double initialHeading, double distance, Datum datum = null)
        {
            Geodesic geodesic = GeodesicForDatum(datum);
            GeodesicData geodesicData = geodesic.Direct(Latitude * R2D, Longitude * R2D, initialHeading * R2D, distance);
            return new Geodetic(geodesicData.Latitude2 * D2R, geodesicData.Longitude2 * D2R, Altitude);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Calculates the end point of travel along the surface of an ellipsoid, from current location over the specified distance, in the direction of
        ///             the specified initial heading.  
        ///             It uses the Charles F.F. Karney algorithm published in "Algorithms for geodesics" and implemented in NETGeographicLib.  
        ///             Accuracy is normally better than 1nm. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 13/05/2019. </remarks>
        ///
        /// <param name="initialHeading">   The initial heading in radians. </param>
        /// <param name="distance">         The distance in metres. </param>
        /// <param name="finalHeading">     [out] The final heading in radians.  Range: ˂0, 2PI). </param>
        /// <param name="datum">            (Optional) The geodetic datum.  Null means WGS84.  
        ///                                 Default value: null. </param>
        ///
        /// <returns>   A geodetic location. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public Geodetic SurfaceTravel(double initialHeading, double distance, out double finalHeading, Datum datum = null)
        {
            Geodesic geodesic = GeodesicForDatum(datum);
            GeodesicData geodesicData = geodesic.Direct(Latitude * R2D, Longitude * R2D, initialHeading * R2D, distance);

            double finalAzimuth = geodesicData.FinalAzimuth;
            if (finalAzimuth < 0.0)
                finalAzimuth += 360.0;
            finalHeading = finalAzimuth * D2R;

            return new Geodetic(geodesicData.Latitude2 * D2R, geodesicData.Longitude2 * D2R, Altitude);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Calculates the distance in metres between current location and the specified one when travelling along the surface of an ellipsoid.  
        ///             It uses the Charles F.F. Karney algorithm published in "Algorithms for geodesics" and implemented in NETGeographicLib.  
        ///             Accuracy is normally better than 1nm. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 13/05/2019. </remarks>
        ///
        /// <param name="destination">  The final position. </param>
        /// <param name="datum">        [Optional] The geodetic datum.  Null means WGS84.  
        ///                             Default value: null. </param>
        ///
        /// <returns>   Distance in metres. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public double SurfaceDistance(in Geodetic destination, Datum datum = null)
        {
            Geodesic geodesic = GeodesicForDatum(datum);
            GeodesicData geodesicData = geodesic.Inverse(Latitude * R2D, Longitude * R2D, destination.Latitude * R2D, destination.Longitude * R2D);
            return geodesicData.Distance;
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Calculates the distance in metres between current location and the specified one when travelling along the surface of an ellipsoid.  
        ///             It uses the Charles F.F. Karney algorithm published in "Algorithms for geodesics" with further addenda and implemented in NETGeographicLib.  
        ///             Accuracy is normally better than 1nm. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 13/05/2019. </remarks>
        ///
        /// <param name="destination">      The final position. </param>
        /// <param name="initialHeading">   [out] The initial heading in radians.  Range: ˂0, 2PI). </param>
        /// <param name="datum">            [Optional] The geodetic datum.  Null means WGS84.  
        ///                                 Default value: null. </param>
        ///
        /// <returns>   Distance in metres. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public double SurfaceDistance(in Geodetic destination, out double initialHeading, Datum datum = null)
        {
            Geodesic geodesic = GeodesicForDatum(datum);
            GeodesicData geodesicData = geodesic.Inverse(Latitude * R2D, Longitude * R2D, destination.Latitude * R2D, destination.Longitude * R2D);

            double initialAzimuth = geodesicData.InitialAzimuth;
            if (initialAzimuth < 0.0)
                initialAzimuth += 360.0;
            initialHeading = initialAzimuth * D2R;

            return geodesicData.Distance;
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Calculates the distance in metres between current location and the specified one when travelling along the surface of an ellipsoid.  
        ///             It uses the Charles F.F. Karney algorithm published in "Algorithms for geodesics" with further addenda and implemented in NETGeographicLib.  
        ///             Accuracy is normally better than 1nm. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 13/05/2019. </remarks>
        ///
        /// <param name="destination">      The final position. </param>
        /// <param name="initialHeading">   [out] The initial heading in radians.  Range: ˂0, 2PI). </param>
        /// <param name="finalHeading">     [out] The final heading in radians.  Range: ˂0, 2PI). </param>
        /// <param name="datum">            (Optional) The geodetic datum.  Null means WGS84.  
        ///                                 Default value: null. </param>
        ///
        /// <returns>   Distance in metres. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public double SurfaceDistance(in Geodetic destination, out double initialHeading, out double finalHeading, Datum datum = null)
        {
            Geodesic geodesic = GeodesicForDatum(datum);
            GeodesicData geodesicData = geodesic.Inverse(Latitude * R2D, Longitude * R2D, destination.Latitude * R2D, destination.Longitude * R2D);

            double initialAzimuth = geodesicData.InitialAzimuth;
            if (initialAzimuth < 0.0)
                initialAzimuth += 360.0;
            initialHeading = initialAzimuth * D2R;

            double finalAzimuth = geodesicData.FinalAzimuth;
            if (finalAzimuth < 0.0)
                finalAzimuth += 360.0;
            finalHeading = finalAzimuth * D2R;

            return geodesicData.Distance;
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Calculates the end point of travel along a straight 3D vector from the current location (projected onto a surface) over the specified vector
        ///             distance, in the surface direction of the specified initial heading.  The end point is also on the surface.  Accuracy: 10nm. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 25/06/2019. </remarks>
        ///
        /// <param name="initialHeading">   The initial heading in radians. </param>
        /// <param name="vectorDistance">   The 3D vector distance in metres. </param>
        /// <param name="datum">            [Optional] The geodetic datum.  Null means WGS84.  
        ///                                 Default value: null. </param>
        ///
        /// <returns>   A geodetic location with altitude 0. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public Geodetic VectorTravel(double initialHeading, double vectorDistance, Datum datum = null)
        {
            if (datum is null)
                datum = Datum.WGS84;

            const double accuracy = 1e-8; // 10nm

            Geodetic surfaceLocation = new(Latitude, Longitude, 0.0);
            Ecef surfaceEcef = surfaceLocation.ToEcef(datum);
            Geodetic destination = surfaceLocation;
            double surfaceDistance = vectorDistance;
            for (double diff = double.MaxValue; Math.Abs(diff) >= accuracy; surfaceDistance += diff)
            {
                destination = SurfaceTravel(initialHeading, surfaceDistance, datum);
                destination = destination.SetAltitude(0.0);
                Ecef destinationEcef = destination.ToEcef(datum);
                diff = vectorDistance - surfaceEcef.DistanceFrom(destinationEcef);
            }

            return destination;
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Tries to retrieve a Geodesic for the specified datum from the geodesic library.  
        ///             If not found, a new Geodesic is created and added to the library. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 13/05/2019. </remarks>
        ///
        /// <param name="datum">    The geodetic datum.  Null means WGS84. </param>
        ///
        /// <returns>   A Geodesic object for the datum. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        private static Geodesic GeodesicForDatum(Datum datum)
        {
            if (datum is null)
                datum = Datum.WGS84;

            if (!geodesicLibrary.TryGetValue(datum, out Geodesic geodesic))
            {
                geodesic = new Geodesic(datum.SemiMajorAxis, datum.Flattening);
                geodesicLibrary[datum] = geodesic;
            }

            return geodesic;
        }

        #endregion Geodesic

        #region Geodetic

        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Returns a copy of this Geodetic with a new altitude. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 24/01/2020. </remarks>
        ///
        /// <param name="altitude"> The altitude in metres. </param>
        ///
        /// <returns>   A new instance of Geodetic. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public Geodetic SetAltitude(double altitude)
        {
            return new Geodetic(Latitude, Longitude, altitude);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Returns the geocentric radius in metres at this location.  
        ///             It is the distance between the Earth centre and the ellipsoid surface at this latitude. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 09/07/2019. </remarks>
        ///
        /// <param name="datum">    [Optional] The geodetic datum.  Null means WGS84.  
        ///                         Default value: null. </param>
        ///
        /// <returns>   Distance in metres. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public double GetGeocentricRadius(Datum datum = null)
        {
            if (datum is null)
                datum = Datum.WGS84;

            double a2 = datum.SemiMajorAxis * datum.SemiMajorAxis;
            double cosLat = Math.Cos(Latitude);
            double a2CosLat2 = a2 * cosLat * cosLat;

            double b2 = datum.SemiMinorAxis * datum.SemiMinorAxis;
            double sinLat = Math.Sin(Latitude);
            double b2SinLat2 = b2 * sinLat * sinLat;

            return Math.Sqrt((a2 * a2CosLat2 + b2 * b2SinLat2) / (a2CosLat2 + b2SinLat2));
        }

        #endregion Geodetic

        #region Convert

        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Instantiates Geodetic coordinates from decimal degrees. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 11/08/2014. </remarks>
        ///
        /// <param name="latitude">     The latitude in degrees. North is positive. </param>
        /// <param name="longitude">    The longitude in degrees. East is positive. </param>
        /// <param name="altitude">     The altitude in metres. </param>
        ///
        /// <returns>   A representation of the geodetic coordinates. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public static Geodetic FromDegrees(double latitude, double longitude, double altitude)
        {
            return new Geodetic((decimal)latitude * D2Rm, (decimal)longitude * D2Rm, altitude);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Converts these geodetic coordinates to geocentric Ecef coordinates using the provided datum and optionally using geoid or elipsoid height. </summary>
        ///
        /// <remarks>   Darran Shepherd, 15/10/2013. </remarks>
        ///
        /// <param name="datum">    [Optional] Datum to be used.  Specify null to use WGS84.  
        ///                         Default value: null. </param>
        /// <param name="geoid">    [Optional] Geoid to be used.  Specify null to use just the ellipsoid.  
        ///                         Default value: null. </param>
        ///
        /// <returns>   This object in Ecef geocentric coordinates. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public Ecef ToEcef(Datum datum = null, Geoid geoid = null)
        {
            if (datum is null)
                datum = Datum.WGS84;

            if (!(geoid is null))
            {
                double h = geoid.GetSeparation(this);
                Geodetic geodetic = new(Latitude, Longitude, Altitude + h);
                return geodetic.ToEcef(datum);
            }

            double cosLatitude = Math.Cos(Latitude);
            double sinLatitude = Math.Sin(Latitude);
            double cosLongitude = Math.Cos(Longitude);
            double sinLongitude = Math.Sin(Longitude);
            double n = datum.SemiMajorAxis / Math.Sqrt(1.0 - datum.FirstEccentricitySquared * sinLatitude * sinLatitude);
            double nhcoslat = (n + Altitude) * cosLatitude;
            double x = nhcoslat * cosLongitude;
            double y = nhcoslat * sinLongitude;
            double z = ((1.0 - datum.FirstEccentricitySquared) * n + Altitude) * sinLatitude;

            return new Ecef(x, y, z);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Converts this geodetic location to topocentric North East Down coordinates relative to the specified reference location. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 04/03/2020. </remarks>
        ///
        /// <param name="referenceLocation">    The reference location. </param>
        /// <param name="datum">                [Optional] The geodetic datum.  Null means WGS84.  
        ///                                     Default value: null. </param>
        /// <param name="geoid">                [Optional] Geoid to be used.  Specify null to use just the ellipsoid.  
        ///                                     Default value: null. </param>
        ///
        /// <returns>   This object as represented in NED coordinates from the reference origin. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public LocalTangentPlane ToNed(in Geodetic referenceLocation, Datum datum = null, Geoid geoid = null)
        {
            Ecef referenceEcef = referenceLocation.ToEcef(datum, geoid);
            return ToNed(referenceLocation, referenceEcef, datum, geoid);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Converts this geodetic location to topocentric North East Down coordinates relative to the specified reference location. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 11/03/2020. </remarks>
        ///
        /// <exception cref="ArgumentException">    Thrown when one or more arguments have unsupported or illegal values. </exception>
        ///
        /// <param name="referenceLocation">    The reference location. </param>
        /// <param name="referenceEcef">        The reference Ecef.  Providing this argument saves the cost of converting the reference location to Ecef. </param>
        /// <param name="datum">                [Optional] The geodetic datum.  Null means WGS84.  
        ///                                     Default value: null. </param>
        /// <param name="geoid">                [Optional] Geoid to be used.  Specify null to use just the ellipsoid.  
        ///                                     Default value: null. </param>
        ///
        /// <returns>   This object as represented in NED coordinates from the reference origin. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public LocalTangentPlane ToNed(in Geodetic referenceLocation, in Ecef referenceEcef, Datum datum = null, Geoid geoid = null)
        {
            if (!referenceEcef.IsAbsolute)
                throw new ArgumentException("Relative Ecefs cannot be used as reference origin", nameof(referenceEcef));

            Ecef thisEcef = ToEcef(datum, geoid);
            Ecef relativeEcef = thisEcef - referenceEcef;
            return relativeEcef.ToNed(referenceLocation);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Outputs this object in human readable form. </summary>
        ///
        /// <remarks>   Darran Shepherd, 15/10/2013. </remarks>
        ///
        /// <returns>   The string representation of these coordinates.  
        ///             North is positive.  East is positive. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public override string ToString()
        {
            return $"Lat:{Latitude * R2D}° Long:{Longitude * R2D}° Alt:{Altitude}m";
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Converts coordinates to a string such as N 51° 59' 22.4" W 000° 59' 29.03". </summary>
        ///
        /// <remarks>   Ralph Gucwa, 03/10/2019. </remarks>
        ///
        /// <param name="secondDecimalPlaces">  [Optional] The maximum number of displayed decimal places for seconds.  
        ///                                     Range: [0,10].  Default value: 5 (corresponds to ~0.3mm). </param>
        ///
        /// <returns>   Coordinates as a string. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public string ToCoordinateString(int secondDecimalPlaces = 5)
        {
            //TODO: convert to Math.Clamp(..) after upgrading to .NET 5
            if (secondDecimalPlaces < 0)
                secondDecimalPlaces = 0;
            if (secondDecimalPlaces > 10)
                secondDecimalPlaces = 10;

            string northSouth = Latitude >= 0.0 ? "N" : "S";
            (int degreesLat, int minutesLat, double secondsLat) = GetDegreesMinutesSeconds(Latitude, secondDecimalPlaces);

            string eastWest = Longitude > 0.0 ? "E" : "W";
            (int degreesLong, int minutesLong, double secondsLong) = GetDegreesMinutesSeconds(Longitude, secondDecimalPlaces);

            string secondsFormat = secondDecimalPlaces == 0 ? "00" : $"00.{new string('#', secondDecimalPlaces)}";
            string secondsLatText = secondsLat.ToString(secondsFormat);
            string secondsLongText = secondsLong.ToString(secondsFormat);

            return $"{northSouth} {degreesLat:00}° {minutesLat:00}' {secondsLatText}\", {eastWest} {degreesLong:000}° {minutesLong:00}' {secondsLongText}\"";
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Creates a complete GGA line with this location at specified time of day.  
        ///             This line is intended to be written to an NMEA file and it is the maximum permitted length ('$' + 79 chars).  
        ///             The end of line characters (CR + LF) are not included.  
        ///             Default latitude/longitude accuracy on the surface: 1.85μm.  Default altitude accuracy: 1μm. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 15/07/2019. </remarks>
        ///
        /// <param name="time">                     Time of day (date is ignored). </param>
        /// <param name="timestampDecimalPlaces">   (Optional) Number of decimal places for the fractional part of the timestamp.  
        ///                                         Range [0-3].  Default: 2, which translates to 10ms or 100Hz. </param>
        /// <param name="latLongDecimalPlaces">     (Optional) Number of decimal places for the fractional part of latitude/longitude minutes.  
        ///                                         Range [1-15].  Default: 9, which translates to 1.85μm on the surface. </param>
        /// <param name="altDecimalPlaces">         (Optional) Number of decimal places for the fractional part of altitude.  
        ///                                         Range [1-15].  Default: 6, which translates to 1μm. </param>
        ///
        /// <returns>   A string with a complete GGA line excluding the ending CR + LF. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public string ToGGALine(DateTime time, int timestampDecimalPlaces = 2, int latLongDecimalPlaces = 9, int altDecimalPlaces = 6)
        {
            //TODO: convert to Math.Clamp(..) after upgrading to .NET 5
            if (latLongDecimalPlaces < 1)
                latLongDecimalPlaces = 1;
            if (latLongDecimalPlaces > 15)
                latLongDecimalPlaces = 15;

            if (altDecimalPlaces < 1)
                altDecimalPlaces = 1;
            if (altDecimalPlaces > 15)
                altDecimalPlaces = 15;

            //time
            string millisecondText;
            if (timestampDecimalPlaces <= 0)
                millisecondText = string.Empty;
            else
            {
                string timeFormat = new('0', timestampDecimalPlaces);
                int divisor = timestampDecimalPlaces switch
                {
                    1 => 100,
                    2 => 10,
                    _ => 1,
                };
                millisecondText = Invariant($".{(time.Millisecond / divisor).ToString(timeFormat, CultureInfo.InvariantCulture)}");
            }

            string latLongMinFormat = Invariant($"00.{new string('0', latLongDecimalPlaces)}");

            //latitude
            (int latDeg, double latMin) = GetDegreesMinutes(Latitude, latLongDecimalPlaces);
            string latMinText = latMin.ToString(latLongMinFormat, CultureInfo.InvariantCulture);
            char ns = Latitude >= 0.0 ? 'N' : 'S';

            //longitude
            (int longDeg, double longMin) = GetDegreesMinutes(Longitude, latLongDecimalPlaces);
            string longMinText = longMin.ToString(latLongMinFormat, CultureInfo.InvariantCulture);
            char ew = Longitude > 0.0 ? 'E' : 'W';

            //altitude
            string altFormat = Invariant($"0.{new string('0', altDecimalPlaces)}");
            string altText = Altitude.ToString(altFormat, CultureInfo.InvariantCulture);

            //GGA
            string ggaData = Invariant($"GPGGA,{time.Hour:00}{time.Minute:00}{time.Second:00}{millisecondText},{latDeg:00}{latMinText},{ns},{longDeg:000}{longMinText},{ew},8,8,,{altText},M,,,,");

            //checksum
            int checksum = 0;
            foreach (int character in ggaData)
                checksum ^= character;

            //whole line
            return $"${ggaData}*{checksum:X2}";
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Gets the number of decimal places for the fractional part of GGA timestamps when using the specified sample rate.  
        ///             The resolution is one millisecond. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 09/05/2022. </remarks>
        ///
        /// <param name="sampleRate">   Sample rate in Hertz.  Range: [1-1000] Hz.  The resulting sample span must be in whole milliseconds. </param>
        ///
        /// <returns>   The number of decimal places [0-3]. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public static int GetGGATimestampDecimalPlaces(int sampleRate)
        {
            int samplePeriodMilliseconds = 1000 / sampleRate;
            int zeroCount = samplePeriodMilliseconds.ToString(CultureInfo.InvariantCulture).Count(ch => ch == '0');
            return 3 - zeroCount;
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Gets the number of decimal places for the fractional part of GGA timestamps when using the specified sample rate.  
        ///             The resolution is one millisecond. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 09/05/2022. </remarks>
        ///
        /// <param name="sampleRate">   Sample rate in Hertz.  Range: [1-1000] Hz.  The resulting sample span must be in whole milliseconds. </param>
        /// <param name="sampleSpan">   [out] The sample span (floored to whole milliseconds). </param>
        ///
        /// <returns>   The number of decimal places [0-3]. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public static int GetGGATimestampDecimalPlaces(int sampleRate, out TimeSpan sampleSpan)
        {
            int samplePeriodMilliseconds = 1000 / sampleRate;
            sampleSpan = TimeSpan.FromMilliseconds(samplePeriodMilliseconds);
            int zeroCount = samplePeriodMilliseconds.ToString(CultureInfo.InvariantCulture).Count(ch => ch == '0');
            return 3 - zeroCount;
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Transforms angle in radians to degrees, minutes and seconds.  The fractional part of seconds uses the specified number of decimal places. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 02/12/2021. </remarks>
        ///
        /// <param name="radians">          The angle in radians. </param>
        /// <param name="numDecimalPlaces"> Number of decimal places used in the fractional part of seconds. </param>
        ///
        /// <returns>   The degrees, minutes and seconds. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        private static (int Degrees, int Minues, double Seconds) GetDegreesMinutesSeconds(double radians, int numDecimalPlaces)
        {
            //rounding of seconds must be performed first to avoid situations when 59.99999999 seconds are rounded to 60 and minutes and degrees are not incremented
            decimal totalSecondsDec = decimal.Round(Math.Abs(3600.0m * R2Dm * (decimal)radians), numDecimalPlaces);
            int truncatedTotalMinutes = (int)(totalSecondsDec * (1.0m / 60.0m));
            int degrees = Math.DivRem(truncatedTotalMinutes, 60, out int minutes);
            double seconds = (double)(totalSecondsDec - 60 * truncatedTotalMinutes);
            if (seconds.IsNegativeZero())
                seconds = 0.0;
            return (degrees, minutes, seconds);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Transforms angle in radians to degrees and minutes.  The fractional part of minutes uses the specified number of decimal places. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 02/12/2021. </remarks>
        ///
        /// <param name="radians">          The angle in radians. </param>
        /// <param name="numDecimalPlaces"> Number of decimal places used in the fractional part of minutes. </param>
        ///
        /// <returns>   The degrees and minutes. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        private static (int Degrees, double Minutes) GetDegreesMinutes(double radians, int numDecimalPlaces)
        {
            //rounding of minutes must be performed first to avoid situations when 59.99999999 minutes are rounded to 60 and degrees are not incremented
            decimal totalMinutesDec = decimal.Round(Math.Abs(60.0m * R2Dm * (decimal)radians), numDecimalPlaces);
            int degrees = (int)(totalMinutesDec * (1.0m / 60.0m));
            double minutes = (double)(totalMinutesDec - 60 * degrees);
            if (minutes.IsNegativeZero())
                minutes = 0.0;
            return (degrees, minutes);
        }

        #endregion Convert

        #region Parse

        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Parses the latitude/longitude from the specified string.  
        ///             A huge number of possible formats is accepted: practically all standard formats plus some exotic formats like those:  
        ///             - milliseconds (e.g. 145505994.48, -268708007.88)  
        ///             - DDMM.xxxx (e.g. 4025.0999N7438.4668W)  
        ///             - DDMMSS.xxxx (e.g. 402505.994N743828.008W)</summary>
        ///
        /// <remarks>   Ralph Gucwa, 07/08/2017. 
        ///             Loosely based on the coordinate-parser https://github.com/servant-of-god/coordinate-parser </remarks>
        ///
        /// <param name="coordinateString"> The string to parse, containing latitude and longitude in any format. </param>
        /// <param name="altitude">         [optional] The altitude in metres.  The default is 0. </param>
        ///
        /// <returns>   A Geodetic with the parsed coordinates or null if the operation failed. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public static Geodetic? Parse(string coordinateString, double altitude = 0.0)
        {
            if (string.IsNullOrWhiteSpace(coordinateString))
                return null;

            double[] allNumbers = ParseNumbers(coordinateString);

            if (!ValidateCoordinateString(coordinateString, allNumbers.Length))
                return null;

            int numberCountPerCoordinate = allNumbers.Length >> 1;

            double latitude = new CoordinateNumber(allNumbers.Take(numberCountPerCoordinate)).ToRadians();
            latitude *= ParseLatitudeSign(coordinateString);

            double longitude = new CoordinateNumber(allNumbers.Skip(numberCountPerCoordinate).Take(numberCountPerCoordinate)).ToRadians();
            longitude *= ParseLongitudeSign(coordinateString);

            return new Geodetic(latitude, longitude, altitude);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Parses all groups of numbers present in the coordinate string whose number group matches are passed as a parameter to this method. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
        ///
        /// <param name="coordinateString"> The string to parse, containing latitude and longitude in any format. </param>
        ///
        /// <returns>   An array with all parsed numbers. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        private static double[] ParseNumbers(string coordinateString)
        {
            if (string.IsNullOrWhiteSpace(coordinateString))
                return Array.Empty<double>();

            CultureInfo culture = CultureInfo.CurrentCulture;
            MatchCollection matches = ParseNumbersRegex.Matches(coordinateString);
            double[] numbers = matches.Cast<Match>().Select(m =>
            {
                const NumberStyles flags = NumberStyles.AllowLeadingSign | NumberStyles.AllowDecimalPoint;

                //decimal dot
                if (double.TryParse(m.Value, flags, CultureInfo.InvariantCulture, out double number))
                    return number;

                //decimal comma
                if (double.TryParse(m.Value, flags, commaCulture, out number))
                    return number;

                //decimal used in current culture
                if (double.TryParse(m.Value, flags, culture, out number))
                    return number;

                //this should never happen
                return double.NaN;
            }).ToArray();

            return numbers;
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Verifies whether the specified coordinate string is in a recognisable format and can be parsed. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
        ///
        /// <param name="coordinateString"> The string to parse, containing latitude and longitude in any format. </param>
        /// <param name="numberGroupCount"> The number of groups of numbers in the coordinate string. </param>
        ///
        /// <returns>   true if the string format is correct and can be parsed, otherwise false. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        private static bool ValidateCoordinateString(string coordinateString, int numberGroupCount)
        {
            //empty?
            if (string.IsNullOrWhiteSpace(coordinateString))
                return false;

            //any extra letters?
            if (Regex.Match(coordinateString, @"(?![neswd])[a-z]", RegexOptions.IgnoreCase).Success)
                return false;

            //correct orientation letters (N, S, E, W) in correct places?
            if (!Regex.Match(coordinateString, @"^[^nsew]*[ns]?[^nsew]*[ew]?[^nsew]*$", RegexOptions.IgnoreCase).Success)
                return false;

            //correct number of number groups?
            return numberGroupCount == 2 || numberGroupCount == 4 || numberGroupCount == 6;
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Parses the latitude sign: 1.0 is returned for North, -1.0 for South. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
        ///
        /// <param name="coordinateString"> The string to parse, containing latitude and longitude in any format. </param>
        ///
        /// <returns>   1.0 for northerly latitude, -1.0 for southerly latitude. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        private static double ParseLatitudeSign(string coordinateString)
        {
            return Regex.Match(coordinateString, @"s", RegexOptions.IgnoreCase).Success ? -1.0 : 1.0;
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Parses the longitude sign: 1.0 is returned for East, -1.0 for West. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
        ///
        /// <param name="coordinateString"> The string to parse, containing latitude and longitude in any format. </param>
        ///
        /// <returns>   1.0 for easterly latitude, -1.0 for westerly latitude. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        private static double ParseLongitudeSign(string coordinateString)
        {
            return Regex.Match(coordinateString, @"w", RegexOptions.IgnoreCase).Success ? -1.0 : 1.0;
        }

        #region CoordinateNumber class

        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   A private class representing an individual coordinate (either latitude or longitude). </summary>
        ///
        /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        private sealed class CoordinateNumber
        {
            #region Private declarations

            private readonly bool isNegative;
            private decimal degrees;
            private decimal minutes;
            private decimal seconds;
            private decimal milliseconds;

            #endregion Private declarations

            #region Constructor

            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            /// <summary>   A private class representing an individual coordinate (either latitude or longitude). </summary>
            ///
            /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
            ///
            /// <param name="coordinateNumbers">    All number groups for this coordinate parsed from a string (no more than 3). </param>
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

            internal CoordinateNumber(IEnumerable<double> coordinateNumbers)
            {
                double[] numbers = new double[3];
                using (IEnumerator<double> enumerator = coordinateNumbers.GetEnumerator())
                    for (int i = 0; enumerator.MoveNext() && i < numbers.Length; i++)
                        numbers[i] = enumerator.Current;

                isNegative = numbers[0] < 0.0;
                degrees = (decimal)Math.Abs(numbers[0]);
                minutes = (decimal)numbers[1];
                seconds = (decimal)numbers[2];

                DetectSpecialFormats();
            }

            #endregion Constructor

            #region Methods

            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            /// <summary>   Detects special formats such as:
            ///             - milliseconds (e.g. 145505994.48, -268708007.88)
            ///             - DDMM.xxxx (e.g. 4025.0999N7438.4668W)
            ///             - DDMMSS.xxxx (e.g. 402505.994N743828.008W)  
            ///             If such a format is detected, the numbers are processed and correct values are assigned to degrees, minutes and seconds fields. </summary>
            ///
            /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

            private void DetectSpecialFormats()
            {
                if (DegreesCanBeSpecial())
                {
                    if (DegreesCanBeMilliseconds())
                        DegreesAsMilliseconds();
                    else if (DegreesCanBeDegreesMinutesAndSeconds())
                        DegreesAsDegreesMinutesAndSeconds();
                    else if (DegreesCanBeDegreesAndMinutes())
                        DegreesAsDegreesAndMinutes();
                }
            }



            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            /// <summary>   Determines if the degrees field can be in a special format.  This usually happens when minutes and seconds are not present. </summary>
            ///
            /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
            ///
            /// <returns>   true if it succeeds, false if it fails. </returns>
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

            private bool DegreesCanBeSpecial()
            {
                return minutes == 0.0m && seconds == 0.0m;
            }



            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            /// <summary>   Determines if the degrees can actually represent the number of milliseconds. </summary>
            ///
            /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
            ///
            /// <returns>   true if it succeeds, false if it fails. </returns>
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

            private bool DegreesCanBeMilliseconds()
            {
                return degrees > 909090.0m;
            }



            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            /// <summary>   Assumes the degrees field represents the number of milliseconds and decomposes it to degrees and milliseconds. </summary>
            ///
            /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

            private void DegreesAsMilliseconds()
            {
                milliseconds = degrees;
                degrees = 0.0m;
            }



            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            /// <summary>   Determines if we degrees field can represent degrees, minutes and seconds in the DDMMSS format. </summary>
            ///
            /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
            ///
            /// <returns>   true if it succeeds, false if it fails. </returns>
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

            private bool DegreesCanBeDegreesMinutesAndSeconds()
            {
                return degrees > 9090.0m;
            }



            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            /// <summary>   Assumes the degrees field represents degrees, minutes and seconds in the DDMMSS format and decomposes it to degrees, minutes and seconds. </summary>
            ///
            /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

            private void DegreesAsDegreesMinutesAndSeconds()
            {
                decimal newDegrees = FastMath.SafeFloor(degrees * 0.0001m);
                minutes = FastMath.SafeFloor((degrees - newDegrees * 100000.0m) * 0.01m);
                seconds = FastMath.SafeFloor(degrees - newDegrees * 10000.0m - minutes * 100.0m);
                degrees = newDegrees;
            }



            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            /// <summary>   Determines if we degrees field can represent degrees and minutes in the DDMM format. </summary>
            ///
            /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
            ///
            /// <returns>   true if it succeeds, false if it fails. </returns>
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

            private bool DegreesCanBeDegreesAndMinutes()
            {
                return degrees > 360.0m;
            }



            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            /// <summary>   Assumes the degrees field represents degrees and minutes in the DDMM format and decomposes it to degrees and minutes. </summary>
            ///
            /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

            private void DegreesAsDegreesAndMinutes()
            {
                decimal newDegrees = FastMath.SafeFloor(degrees * 0.01m);
                minutes = degrees - newDegrees * 100.0m;
                degrees = newDegrees;
            }



            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            /// <summary>   Converts this CoordinateNumber to total degrees. </summary>
            ///
            /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
            ///
            /// <returns>   The coordinate expressed in total degrees. </returns>
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

            internal double ToDegrees()
            {
                double totalDegrees = (double)(degrees + minutes * (1.0m / 60.0m) + seconds * (1.0m / 3600.0m) + milliseconds * (1.0m / 3600000.0m));
                return isNegative ? -totalDegrees : totalDegrees;
            }




            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            /// <summary>   Converts this CoordinateNumber to radians. </summary>
            ///
            /// <remarks>   Ralph Gucwa, 07/08/2017. </remarks>
            ///
            /// <returns>   The coordinate expressed in radians. </returns>
            ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

            internal double ToRadians()
            {
                decimal totalDegrees = degrees + minutes * (1.0m / 60.0m) + seconds * (1.0m / 3600.0m) + milliseconds * (1.0m / 3600000.0m);
                double radians = (double)(totalDegrees * D2Rm);
                return isNegative ? -radians : radians;
            }

            #endregion Methods
        }

        #endregion CoordinateNumber class

        #endregion Parse

        #region Equality

        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Determines whether the specified object is equal to the current object. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 25/10/2017. </remarks>
        ///
        /// <param name="obj">  The object to compare with the current object. </param>
        ///
        /// <returns>   true if the specified object is equal to the current object; otherwise, false. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public override bool Equals(object obj)
        {
            return obj is Geodetic other && Equals(other);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Tests if this Geodetic is considered equal to another. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 25/10/2017. </remarks>
        ///
        /// <param name="other">    The other Geodetic. </param>
        ///
        /// <returns>   true if the Geodetics are considered equal, false if they are not. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public bool Equals(Geodetic other)
        {
            return other.Latitude.Equals(Latitude)
                && other.Longitude.Equals(Longitude)
                && other.Altitude.Equals(Altitude);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Equality operator. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 25/10/2017. </remarks>
        ///
        /// <param name="left">     The left Geodetic. </param>
        /// <param name="right">    The right Geodetic. </param>
        ///
        /// <returns>   True if the Geodetics are equal. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public static bool operator ==(Geodetic left, Geodetic right)
        {
            return left.Equals(right);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Inequality operator. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 25/10/2017. </remarks>
        ///
        /// <param name="left">     The left Geodetic. </param>
        /// <param name="right">    The right Geodetic. </param>
        ///
        /// <returns>   True if the Geodetics are different. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public static bool operator !=(Geodetic left, Geodetic right)
        {
            return !(left == right);
        }



        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        /// <summary>   Returns the hash code for this instance. </summary>
        ///
        /// <remarks>   Ralph Gucwa, 25/10/2017. </remarks>
        ///
        /// <returns>   A 32-bit signed integer that is the hash code for this instance. </returns>
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        public override int GetHashCode()
        {
            unchecked
            {
                int hash = 601 * 9973 + Latitude.GetHashCode();
                hash = hash * 9973 + Longitude.GetHashCode();
                hash = hash * 9973 + Altitude.GetHashCode();
                return hash;
            }
        }

        #endregion Equality

        #endregion Methods
    }
}
