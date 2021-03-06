/*
This code is largely based on the original code by Quentin "Leph" Rouxel and Team Rhoban.
The original files can be found at:
https://github.com/Rhoban/model/
*/
#ifndef NEWTONBINOMIAL_HPP
#define NEWTONBINOMIAL_HPP

#include "Combination.hpp"
#include "Polynom.hpp"

namespace bitbots_splines {

/**
 * NewtonBinomial
 *
 * Implement Newton binomial
 * simple formulae and binding
 * with polynom structure
 */
class NewtonBinomial
{
    public:

        /**
         * Expand the given formula (x + y)^degree
         * and return the polynom in x whose coefficient
         * are computed using binomial coefficient
         */
        static Polynom expandPolynom(
            double y, unsigned int degree);

    private:
};

}

#endif

