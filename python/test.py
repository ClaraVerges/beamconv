import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import healpy as hp
import tools
from instrument import ScanStrategy

def scan1(lmax=700, mmax=5, fwhm=40, nside=256, ra0=-10, dec0=-57.5,
    az_throw=10, scan_speed=1, rot_period=10*60):
    '''
    Simulates a fraction of BICEP2-like scan strategy

    Arguments
    ---------

    lmax : int
        bandlimit
    mmax : int
        assumed azimuthal bandlimit beams (symmetric in this example)
    fwhm : float
        The beam FWHM in arcmin
    nside : int
        The nside value of the output map
    rot_perio : int
        The instrument rotation period [s]


    '''

    # Load up alm and blm
    cls = np.loadtxt('../ancillary/wmap7_r0p03_lensed_uK_ext.txt', unpack=True) # Cl in uK^2
    ell, cls = cls[0], cls[1:]
    alm = hp.synalm(cls, lmax=lmax, new=True, verbose=True) # uK

    blm, blmm2 = tools.gauss_blm(fwhm, lmax, pol=True)
    blm = tools.get_copol_blm(blm.copy())

    # init scan strategy and instrument
    b2 = ScanStrategy(20*60*60, # mission duration in sec.
                      sample_rate=10, # 10 Hz sample rate
                      location='spole', # South pole instrument
                      )

    # Calculate spinmaps, stored internally
    print('\nCalculating spin-maps...')
    sys.stdout = open(os.devnull, 'w') # Suppressing screen output
    b2.get_spinmaps(alm, blm, mmax)
    sys.stdout = sys.__stdout__
    print('...spin-maps stored')

    # Initiate a single detector
    b2.set_focal_plane(nrow=1, ncol=1, fov=10)
    az_off = b2.chn_pr_az
    el_off = b2.chn_pr_el

    b2.set_instr_rot(period=rot_period) # Rotate instrument (period in sec)

    chunks = b2.partition_mission(int(60*60*b2.fsamp)) # calculate tod in chunks of # samples

    # Allocate for mapmaking
    vec = np.zeros((3, 12*b2.nside_out**2), dtype=float)
    proj = np.zeros((6, 12*b2.nside_out**2), dtype=float)

    for cidx, chunk in enumerate(chunks):
        print('  Working on chunk {:03}: samples {:d}-{:d}'.format(cidx,
          chunk['start'], chunk['end']))

        # Make the boresight move
        b2.constant_el_scan(ra0=ra0, dec0=dec0, az_throw=az_throw,
          scan_speed=scan_speed, el_step=1*(cidx % 50 - 25), **chunk)

        # if required, loop over boresight rotations
        for subchunk in b2.subpart_chunk(chunk):

            # Do the actual scanning
            b2.scan(az_off=az_off, el_off=el_off, **subchunk)
            b2.bin_tod(az_off, el_off)

            # this is a bit simplistic now, but works
            vec += b2.depo['vec']
            proj += b2.depo['proj']

    # just solve for the unpolarized map for now (condition number is terrible obviously)
    maps = b2.solve_map(vec=vec[0], proj=proj[0], copy=True)

    # plot solved T map
    moll_opts = dict(min=-250, max=250)

    plt.figure()
    hp.mollview(maps, **moll_opts)
    plt.savefig('../scratch/img/test_map_I.png')
    plt.close()

    # plot the input map and spectra
    maps_raw = hp.alm2map(alm, 256)
    plt.figure()
    hp.mollview(maps_raw[0], **moll_opts)
    plt.savefig('../scratch/img/raw_map_I.png')
    plt.close()

    cls[3][cls[3]<=0.] *= -1.
    dell = ell * (ell + 1) / 2. / np.pi
    plt.figure()
    for i, label in enumerate(['TT', 'EE', 'BB', 'TE']):
      plt.semilogy(ell, dell * cls[i], label=label)

    plt.legend()
    plt.ylabel(r'$D_{\ell}$ [$\mu K^2_{\mathrm{CMB}}$]')
    plt.xlabel(r'Multipole [$\ell$]')
    plt.savefig('../scratch/img/cls.png')
    plt.close()

def scan2(lmax=700, mmax=5, fwhm=40, nside=256, ra0=-10, dec0=-57.5,
    az_throw=10, scan_speed=1, rot_period=10*60):
    '''
    Simulates a fraction of BICEP2-like scan strategy

    Arguments
    ---------

    lmax : int
        bandlimit
    mmax : int
        assumed azimuthal bandlimit beams (symmetric in this example)
    fwhm : float
        The beam FWHM in arcmin
    nside : int
        The nside value of the output map
    rot_perio : int
        The instrument rotation period [s]


    '''

    # Load up alm and blm
    cls = np.loadtxt('../ancillary/wmap7_r0p03_lensed_uK_ext.txt', unpack=True) # Cl in uK^2
    ell, cls = cls[0], cls[1:]
    alm = hp.synalm(cls, lmax=lmax, new=True, verbose=True) # uK

    blm, blmm2 = tools.gauss_blm(fwhm, lmax, pol=True)
    blm = tools.get_copol_blm(blm.copy())

    # init scan strategy and instrument
    b2 = ScanStrategy(20*60*60, # mission duration in sec.
                      sample_rate=10, # 10 Hz sample rate
                      location='spole', # South pole instrument
                      )

    # Calculate spinmaps, stored internally
    print('\nCalculating spin-maps...')
    sys.stdout = open(os.devnull, 'w') # Suppressing screen output
    b2.get_spinmaps(alm, blm, mmax)
    sys.stdout = sys.__stdout__
    print('...spin-maps stored')

    # Initiate a single detector
    b2.set_focal_plane(nrow=1, ncol=1, fov=10)
    az_off = b2.chn_pr_az
    el_off = b2.chn_pr_el

    b2.set_instr_rot(period=rot_period) # Rotate instrument (period in sec)

    chunks = b2.partition_mission(int(60*60*b2.fsamp)) # calculate tod in chunks of # samples
    b2.allocate_maps() # Allocate for mapmaking
    b2.scan_instrument() # Generating timestreams and maps

    # just solve for the unpolarized map for now (condition number is terrible obviously)
    maps = b2.solve_map(vec=vec[0], proj=proj[0], copy=True)

    # plot solved T map
    moll_opts = dict(min=-250, max=250)

    plt.figure()
    hp.mollview(maps, **moll_opts)
    plt.savefig('../scratch/img/test_map_I.png')
    plt.close()

    # plot the input map and spectra
    maps_raw = hp.alm2map(alm, 256)
    plt.figure()
    hp.mollview(maps_raw[0], **moll_opts)
    plt.savefig('../scratch/img/raw_map_I.png')
    plt.close()

    cls[3][cls[3]<=0.] *= -1.
    dell = ell * (ell + 1) / 2. / np.pi
    plt.figure()
    for i, label in enumerate(['TT', 'EE', 'BB', 'TE']):
      plt.semilogy(ell, dell * cls[i], label=label)

    plt.legend()
    plt.ylabel(r'$D_{\ell}$ [$\mu K^2_{\mathrm{CMB}}$]')
    plt.xlabel(r'Multipole [$\ell$]')
    plt.savefig('../scratch/img/cls.png')
    plt.close()


if __name__ == '__main__':

    scan1()
